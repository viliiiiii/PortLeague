from django.core.management.base import BaseCommand
from core.models import Team
from accounts.models import UserProfile
import requests
from django.conf import settings
from django.db import transaction

class Command(BaseCommand):
    help = 'Updates all team IDs to match the football API IDs'

    def handle(self, *args, **options):
        # Fetch teams from the API
        API_URL = "https://api.football-data.org/v4/competitions/PPL/teams"
        HEADERS = {"X-Auth-Token": settings.FOOTBALL_API_KEY}

        try:
            self.stdout.write('Fetching teams from API...')
            response = requests.get(API_URL, headers=HEADERS)
            response.raise_for_status()
            api_teams = response.json().get('teams', [])

            # Create a mapping of team names to API IDs
            team_mapping = {}
            old_to_new_id_mapping = {}  # To store old ID to new ID mapping
            for team in api_teams:
                team_mapping[team['name']] = {
                    'id': team['id'],
                    'crest': team.get('crest', ''),
                    'tla': team.get('tla', ''),
                    'founded': team.get('founded'),
                    'venue': team.get('venue', '')
                }

            # Update local teams
            updated_count = 0
            not_found_teams = []

            with transaction.atomic():  # Use transaction to ensure data consistency
                # get all UserProfiles with favorite teams
                profiles_with_teams = UserProfile.objects.select_related('favorite_team').filter(favorite_team__isnull=False)
                profile_updates = []  # Store profile updates for later

                # Update teams and build old-to-new ID mapping
                for db_team in Team.objects.all():
                    # Try to find the team in our mapping
                    api_team = team_mapping.get(db_team.name)
                    
                    if api_team:
                        old_id = db_team.id
                        old_to_new_id_mapping[old_id] = api_team['id']
                        
                        # Update team information
                        db_team.id = api_team['id']
                        db_team.crest = api_team['crest']
                        db_team.tla = api_team['tla']
                        db_team.founded = api_team['founded']
                        db_team.venue = api_team['venue']
                        db_team.save()
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Updated {db_team.name}: ID {old_id} → {api_team["id"]}'
                            )
                        )
                        updated_count += 1
                    else:
                        not_found_teams.append(db_team.name)

                # Now update UserProfiles with new team IDs
                for profile in profiles_with_teams:
                    old_team_id = profile.favorite_team_id
                    if old_team_id in old_to_new_id_mapping:
                        new_team_id = old_to_new_id_mapping[old_team_id]
                        profile.favorite_team_id = new_team_id
                        profile.save()
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Updated user {profile.user.username}\'s favorite team ID: {old_team_id} → {new_team_id}'
                            )
                        )

            # Summary
            self.stdout.write('\nUpdate Summary:')
            self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count} teams'))
            
            if not_found_teams:
                self.stdout.write(
                    self.style.WARNING(
                        f'\nTeams not found in API ({len(not_found_teams)}):'
                    )
                )
                for team in not_found_teams:
                    self.stdout.write(f'- {team}')

            # Print available API teams that aren't in database
            db_team_names = set(Team.objects.values_list('name', flat=True))
            missing_teams = set(team_mapping.keys()) - db_team_names
            
            if missing_teams:
                self.stdout.write(
                    self.style.WARNING(
                        f'\nTeams in API but not in database ({len(missing_teams)}):'
                    )
                )
                for team in sorted(missing_teams):
                    self.stdout.write(f'- {team} (ID: {team_mapping[team]["id"]})')

        except requests.exceptions.RequestException as e:
            self.stdout.write(
                self.style.ERROR(f'Error fetching data from API: {str(e)}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error updating team IDs: {str(e)}')
            ) 