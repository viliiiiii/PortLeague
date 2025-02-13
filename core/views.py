from django.shortcuts import render
from django.conf import settings
import requests
from datetime import datetime, timezone

def fetch_fixtures():
    API_URL = "https://api.football-data.org/v4/competitions/PPL/matches"
    HEADERS = {"X-Auth-Token": settings.FOOTBALL_API_KEY}

    try:
        response = requests.get(API_URL, headers=HEADERS)
        response.raise_for_status()
        data = response.json()

        current_date = datetime.now(timezone.utc)

        matches_by_matchday = {}
        for match in data.get("matches", []):
            matchday = match["matchday"]
            match_datetime = datetime.strptime(match["utcDate"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            match["formatted_date"] = match_datetime.strftime("%Y/%m/%d, %H:%M")

            # Extract status and scores correctly
            match["match_status"] = match.get("status", "UNKNOWN")
            full_time_score = match.get("score", {}).get("fullTime", {})
            match["home_score"] = full_time_score.get("home") if full_time_score.get("home") is not None else "N/A"
            match["away_score"] = full_time_score.get("away") if full_time_score.get("away") is not None else "N/A"

            # If match is finished and scores are missing, show "N/A"
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

        # Find latest matchweek and upcoming matchweek
        latest_matchweek = None
        upcoming_matchweek = None

        for matchday, matches in sorted(matches_by_matchday.items(), reverse=True):
            if all(datetime.strptime(m["utcDate"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc) < current_date for m in matches):
                latest_matchweek = matchday
                break

        for matchday, matches in sorted(matches_by_matchday.items()):
            if any(datetime.strptime(m["utcDate"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc) >= current_date for m in matches):
                upcoming_matchweek = matchday
                break

        return matches_by_matchday.get(latest_matchweek, []), matches_by_matchday.get(upcoming_matchweek, [])

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return [], []


def home(request):
    recent_matches, upcoming_matches = fetch_fixtures()
    return render(request, "core/home.html", {
        "recent_matches": recent_matches,
        "upcoming_matches": upcoming_matches
    })

def all_fixtures(request):
    API_URL = "https://api.football-data.org/v4/competitions/PPL/matches"
    HEADERS = {"X-Auth-Token": settings.FOOTBALL_API_KEY}

    try:
        response = requests.get(API_URL, headers=HEADERS)
        response.raise_for_status()
        data = response.json()

        # Format dates
        for match in data.get("matches", []):
            match_datetime = datetime.strptime(match["utcDate"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            match["formatted_date"] = match_datetime.strftime("%Y/%m/%d, %H:%M")

        # Extract status and scores correctly
            match["match_status"] = match.get("status", "UNKNOWN")
            full_time_score = match.get("score", {}).get("fullTime", {})

        # Use "home" and "away" instead of "homeTeam" and "awayTeam"
            match["home_score"] = full_time_score.get("home") if full_time_score.get("home") is not None else "N/A"
            match["away_score"] = full_time_score.get("away") if full_time_score.get("away") is not None else "N/A"

        return render(request, "core/all_fixtures.html", {"all_matches": data.get("matches", [])})

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return render(request, "core/all_fixtures.html", {"all_matches": []})
