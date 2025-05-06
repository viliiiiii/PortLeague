from django.core.management.base import BaseCommand
from django.conf import settings
import requests
from core.models import Team

class Command(BaseCommand):
    help = 'Populates the database with teams from football-data.org API'

    def handle(self, *args, **options):
        API_URL = "https://api.football-data.org/v4/competitions/PPL/teams"
        HEADERS = {"X-Auth-Token": settings.FOOTBALL_API_KEY}

        try:
            response = requests.get(API_URL, headers=HEADERS)
            response.raise_for_status()
            data = response.json()

            for team_data in data.get("teams", []):
                team, created = Team.objects.get_or_create(
                    name=team_data["name"],
                    defaults={
                        "name": team_data["name"]
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created team: {team.name}'))
                else:
                    self.stdout.write(self.style.WARNING(f'Team already exists: {team.name}'))

            self.stdout.write(self.style.SUCCESS('Successfully populated teams'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error populating teams: {str(e)}')) 