from django.shortcuts import render
from django.conf import settings
import requests
from django.core.cache import cache

def fetch_standings(season=None):
    cache_key = f"standings_{season}" if season else "standings_current"
    cached_standings = cache.get(cache_key)

    if cached_standings:
        return cached_standings

    API_URL = "https://api.football-data.org/v4/competitions/PPL/standings"
    if season:
        API_URL += f"?season={season}"

    HEADERS = {"X-Auth-Token": settings.FOOTBALL_API_KEY}

    try:
        response = requests.get(API_URL, headers=HEADERS)
        response.raise_for_status()
        data = response.json()

        standings = {"TOTAL": [], "HOME": [], "AWAY": []}

        for table in data.get("standings", []):
            if table["type"] == "TOTAL":
                standings["TOTAL"] = table["table"]
            elif table["type"] == "HOME":
                standings["HOME"] = table["table"]
            elif table["type"] == "AWAY":
                standings["AWAY"] = table["table"]

        cache.set(cache_key, standings, timeout=3600)  # Cache for 1 hour
        return standings

    except requests.exceptions.RequestException as e:
        print(f"Error fetching standings: {e}")
        return {"TOTAL": [], "HOME": [], "AWAY": []}

def standings(request):
    season = request.GET.get("season", None)  # Default to current season
    standings = fetch_standings(season)
    standings_type = request.GET.get("type", "TOTAL")

    return render(request, "standings/standings.html", {
        "standings": standings[standings_type],
        "standings_type": standings_type,
        "selected_season": season,
    })

def fetch_team_details(team_id):
    """Fetches basic team details (name, logo, venue, coach)."""
    API_URL = f"https://api.football-data.org/v4/teams/{team_id}"
    HEADERS = {"X-Auth-Token": settings.FOOTBALL_API_KEY}

    try:
        response = requests.get(API_URL, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching team data: {e}")
        return None

from datetime import datetime

def fetch_team_matches(team_id, status):
    """Fetch recent or upcoming matches for a specific team."""
    API_URL = f"https://api.football-data.org/v4/teams/{team_id}/matches?status={status}"
    HEADERS = {"X-Auth-Token": settings.FOOTBALL_API_KEY}

    try:
        response = requests.get(API_URL, headers=HEADERS)
        response.raise_for_status()
        matches = response.json().get("matches", [])

        for match in matches:
            match_datetime = datetime.strptime(match["utcDate"], "%Y-%m-%dT%H:%M:%SZ")
            match["formatted_date"] = match_datetime.strftime("%Y/%m/%d, %H:%M")  # Format same as home page

        return matches[:5]  # Return only last 5 matches
    except requests.exceptions.RequestException as e:
        print(f"Error fetching team matches: {e}")
        return []

def team_details(request, team_id):
    """Displays details of a selected team, including recent matches, upcoming matches, and squad list."""
    team = fetch_team_details(team_id)
    recent_matches = fetch_team_matches(team_id, "FINISHED")
    upcoming_matches = fetch_team_matches(team_id, "SCHEDULED")

    if not team:
        return render(request, "standings/team_details.html", {"error": "Team not found"})

    # 🔹 Extract squad and calculate ages
    squad = team.get("squad", [])
    for player in squad:
        dob = player.get("dateOfBirth")  # Format: "YYYY-MM-DD"
        if dob:
            birth_year = int(dob[:4])
            player["age"] = 2025 - birth_year  # Calculate Age
        else:
            player["age"] = "N/A"

    return render(request, "standings/team_details.html", {
        "team": team,
        "recent_matches": recent_matches,
        "upcoming_matches": upcoming_matches,
        "squad": squad,
    })