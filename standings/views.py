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

        cache.set(cache_key, standings, timeout=3600)
        return standings

    except requests.exceptions.RequestException as e:
        print(f"Error fetching standings: {e}")
        return {"TOTAL": [], "HOME": [], "AWAY": []}

def standings(request):
    # Get filter parameters from request
    standings_type = request.GET.get('type', 'TOTAL')
    selected_season = request.GET.get('season', '2024')
    search_query = request.GET.get('search', '').lower()
    min_points = request.GET.get('min_points')
    max_points = request.GET.get('max_points')
    min_position = request.GET.get('min_position')
    max_position = request.GET.get('max_position')

    API_URL = f"https://api.football-data.org/v4/competitions/PPL/standings"
    if selected_season:
        API_URL += f"?season={selected_season}"
    HEADERS = {"X-Auth-Token": settings.FOOTBALL_API_KEY}

    try:
        response = requests.get(API_URL, headers=HEADERS)
        response.raise_for_status()
        data = response.json()

        # Get standings based on type (TOTAL, HOME, AWAY)
        standings_data = None
        for standing in data.get("standings", []):
            if standing["type"] == standings_type:
                standings_data = standing["table"]
                break

        # If no standings found for the selected type, return empty list
        if not standings_data:
            return render(request, "standings/standings.html", {
                "standings": [],
                "standings_type": standings_type,
                "selected_season": selected_season,
                "error": f"No standings found for type: {standings_type}"
            })

        filtered_standings = []
        for team in standings_data:
            # Apply search filter
            if search_query and search_query not in team["team"]["name"].lower():
                continue

            # Apply points range filter
            if min_points and int(team["points"]) < int(min_points):
                continue
            if max_points and int(team["points"]) > int(max_points):
                continue

            # Apply position range filter
            if min_position and int(team["position"]) < int(min_position):
                continue
            if max_position and int(team["position"]) > int(max_position):
                continue

            filtered_standings.append(team)

        return render(request, "standings/standings.html", {
            "standings": filtered_standings,
            "standings_type": standings_type,
            "selected_season": selected_season
        })

    except requests.exceptions.RequestException as e:
        print(f"Error fetching standings: {e}")
        return render(request, "standings/standings.html", {
            "standings": [],
            "standings_type": standings_type,
            "selected_season": selected_season,
            "error": "Error fetching standings data"
        })

def fetch_team_details(team_id):
    """Fetches basic team details (name, logo, venue, coach)."""
    cache_key = f"team_details_{team_id}"
    cached_team = cache.get(cache_key)

    if cached_team:
        return cached_team

    API_URL = f"https://api.football-data.org/v4/teams/{team_id}"
    HEADERS = {"X-Auth-Token": settings.FOOTBALL_API_KEY}

    try:
        response = requests.get(API_URL, headers=HEADERS)
        response.raise_for_status()
        team_data = response.json()
        cache.set(cache_key, team_data, timeout=86400)  # Cache for 24 hours
        return team_data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching team data: {e}")
        return None

from datetime import datetime

def fetch_team_matches(team_id, status):
    """Fetch recent or upcoming matches for a specific team."""
    cache_key = f"team_matches_{team_id}_{status}"
    cached_matches = cache.get(cache_key)

    if cached_matches:
        return cached_matches

    API_URL = f"https://api.football-data.org/v4/teams/{team_id}/matches?status={status}"
    HEADERS = {"X-Auth-Token": settings.FOOTBALL_API_KEY}

    try:
        response = requests.get(API_URL, headers=HEADERS)
        response.raise_for_status()
        matches = response.json().get("matches", [])

        for match in matches:
            match_datetime = datetime.strptime(match["utcDate"], "%Y-%m-%dT%H:%M:%SZ")
            match["formatted_date"] = match_datetime.strftime("%Y/%m/%d, %H:%M")

        matches = matches[:5]  # Return only last 5 matches
        cache.set(cache_key, matches, timeout=3600)  # Cache for 1 hour
        return matches
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

    # Fetching squad and converting age
    squad = team.get("squad", [])
    for player in squad:
        dob = player.get("dateOfBirth") 
        if dob:
            birth_year = int(dob[:4])
            player["age"] = 2025 - birth_year 
        else:
            player["age"] = "N/A"

    return render(request, "standings/team_details.html", {
        "team": team,
        "recent_matches": recent_matches,
        "upcoming_matches": upcoming_matches,
        "squad": squad,
    })