from django.shortcuts import render
from django.conf import settings
import requests
from datetime import datetime
import pytz
from django.utils import timezone
from standings.views import fetch_standings
from django.core.cache import cache

def fetch_fixtures():
    """
    Fetch football fixtures from the API with caching.
    Returns recent and upcoming matches with formatted dates and scores.
    """
    cache_key = "fixtures_data"
    cached_data = cache.get(cache_key)

    if cached_data:
        return cached_data

    API_URL = "https://api.football-data.org/v4/competitions/PPL/matches"
    HEADERS = {"X-Auth-Token": settings.FOOTBALL_API_KEY}

    try:
        response = requests.get(API_URL, headers=HEADERS)
        response.raise_for_status()
        data = response.json()

        current_date = datetime.now(pytz.UTC)

        matches_by_matchday = {}
        for match in data.get("matches", []):
            matchday = match["matchday"]
            match_datetime = datetime.strptime(match["utcDate"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.UTC)
            match["formatted_date"] = match_datetime.strftime("%Y/%m/%d, %H:%M")

            #Fetch status and scores 
            match["match_status"] = match.get("status", "UNKNOWN")
            full_time_score = match.get("score", {}).get("fullTime", {})
            match["home_score"] = full_time_score.get("home") if full_time_score.get("home") is not None else "N/A"
            match["away_score"] = full_time_score.get("away") if full_time_score.get("away") is not None else "N/A"

            # Check if match is finished
            if match["match_status"] == "FINISHED":
                if match["home_score"] is None:
                    match["home_score"] = "N/A"
                if match["away_score"] is None:
                    match["away_score"] = "N/A"
            else:
                match["home_score"] = "TBD"
                match["away_score"] = "TBD"

            if matchday not in matches_by_matchday:
                matches_by_matchday[matchday] = []
            matches_by_matchday[matchday].append(match)

        #Find latest and upcoming gameweek
        latest_matchweek = None
        upcoming_matchweek = None

        for matchday, matches in sorted(matches_by_matchday.items(), reverse=True):
            if all(datetime.strptime(m["utcDate"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.UTC) < current_date for m in matches):
                latest_matchweek = matchday
                break

        for matchday, matches in sorted(matches_by_matchday.items()):
            if any(datetime.strptime(m["utcDate"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.UTC) >= current_date for m in matches):
                upcoming_matchweek = matchday
                break

        result = (matches_by_matchday.get(latest_matchweek, []), matches_by_matchday.get(upcoming_matchweek, []))
        cache.set(cache_key, result, timeout=300)  # Cache for 5 minutes
        return result

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return [], []


def home(request):
    recent_matches, upcoming_matches = fetch_fixtures()
    
    # Get user's favorite team if logged in
    favorite_team = None
    favorite_team_stats = None
    if request.user.is_authenticated:
        try:
            favorite_team = request.user.userprofile.favorite_team
            
            if favorite_team:
                # Get standings data
                standings_data = fetch_standings()
                
                if standings_data and "TOTAL" in standings_data:
                    for team in standings_data["TOTAL"]:
                        if team["team"]["id"] == favorite_team.id:
                            favorite_team_stats = team
                            break

                # Filter matches for favourite team
                favorite_recent_matches = [
                    match for match in recent_matches
                    if str(match["homeTeam"]["id"]) == str(favorite_team.id) or str(match["awayTeam"]["id"]) == str(favorite_team.id)
                ][:3]  # Last 3 matches

                favorite_upcoming_matches = [
                    match for match in upcoming_matches
                    if str(match["homeTeam"]["id"]) == str(favorite_team.id) or str(match["awayTeam"]["id"]) == str(favorite_team.id)
                ][:3]  # Next 3 matches

                # Remove favourite team matches from the main lists to avoid duplication
                recent_matches = [
                    match for match in recent_matches
                    if str(match["homeTeam"]["id"]) != str(favorite_team.id) and str(match["awayTeam"]["id"]) != str(favorite_team.id)
                ]
                upcoming_matches = [
                    match for match in upcoming_matches
                    if str(match["homeTeam"]["id"]) != str(favorite_team.id) and str(match["awayTeam"]["id"]) != str(favorite_team.id)
                ]

                context = {
                    "recent_matches": recent_matches,
                    "upcoming_matches": upcoming_matches,
                    "favorite_team": favorite_team,
                    "favorite_team_stats": favorite_team_stats,
                    "favorite_recent_matches": favorite_recent_matches,
                    "favorite_upcoming_matches": favorite_upcoming_matches,
                }
                return render(request, "core/home.html", context)

        except Exception as e:
            pass

    return render(request, "core/home.html", {
        "recent_matches": recent_matches,
        "upcoming_matches": upcoming_matches,
    })

def all_fixtures(request):
    """
    View all fixtures with filtering options.
    """
    API_URL = "https://api.football-data.org/v4/competitions/PPL/matches"
    HEADERS = {"X-Auth-Token": settings.FOOTBALL_API_KEY}

    try:
        response = requests.get(API_URL, headers=HEADERS)
        response.raise_for_status()
        data = response.json()

        # Group matches by gameweek
        matches_by_gameweek = {}
        for match in data.get("matches", []):
            matchday = match["matchday"]
            match_datetime = datetime.strptime(match["utcDate"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.UTC)
            match["formatted_date"] = match_datetime.strftime("%Y/%m/%d, %H:%M")

            # Fetch status and scores
            match["match_status"] = match.get("status", "UNKNOWN")
            full_time_score = match.get("score", {}).get("fullTime", {})
            match["home_score"] = full_time_score.get("home") if full_time_score.get("home") is not None else "N/A"
            match["away_score"] = full_time_score.get("away") if full_time_score.get("away") is not None else "N/A"

            if matchday not in matches_by_gameweek:
                matches_by_gameweek[matchday] = []
            matches_by_gameweek[matchday].append(match)

        # Get current gameweek from request or default to first gameweek
        current_gameweek = int(request.GET.get('gameweek', 1))
        total_gameweeks = max(matches_by_gameweek.keys()) if matches_by_gameweek else 1
        
        # Create gameweek range for dropdown
        gameweek_range = range(1, total_gameweeks + 1)
        
        # Ensure current_gameweek is within valid range
        current_gameweek = max(1, min(current_gameweek, total_gameweeks))
        
        # Get matches for current gameweek
        current_matches = matches_by_gameweek.get(current_gameweek, [])

        # Apply filters
        search_query = request.GET.get('search', '').lower()
        status_filter = request.GET.get('status', 'all')

        filtered_matches = []
        for match in current_matches:
            # Apply search filter
            if search_query:
                home_team = match['homeTeam']['name'].lower()
                away_team = match['awayTeam']['name'].lower()
                if search_query not in home_team and search_query not in away_team:
                    continue

            # Apply status filter
            if status_filter != 'all':
                if status_filter == 'upcoming' and match['match_status'] == 'FINISHED':
                    continue
                if status_filter == 'finished' and match['match_status'] != 'FINISHED':
                    continue

            filtered_matches.append(match)

        return render(request, "core/all_fixtures.html", {
            "matches": filtered_matches,
            "current_gameweek": current_gameweek,
            "total_gameweeks": total_gameweeks,
            "prev_gameweek": max(1, current_gameweek - 1),
            "next_gameweek": min(total_gameweeks, current_gameweek + 1),
            "gameweek_range": gameweek_range
        })

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return render(request, "core/all_fixtures.html", {
            "matches": [],
            "current_gameweek": 1,
            "total_gameweeks": 1,
            "prev_gameweek": 1,
            "next_gameweek": 1,
            "gameweek_range": range(1, 2)  # Just one gameweek in case of error
        })

def games(request):
    return render(request, 'core/games.html')
