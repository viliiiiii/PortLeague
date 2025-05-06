from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
import requests
from .forms import CustomUserCreationForm
from .models import UserProfile
from core.models import Team
from games.models import PollVote, QuizScore
from django.conf import settings

def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Create or update user profile
            UserProfile.objects.get_or_create(
                user=user,
                defaults={'favorite_team': form.cleaned_data.get("favorite_team")}
            )
            
            messages.success(request, 'Account created successfully. You can now login.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, "accounts/register.html", {"form": form})

@login_required
def profile(request):
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)

    if request.method == "POST":
        if "update_info" in request.POST:
            # Handle username and email update
            username = request.POST.get("username")
            email = request.POST.get("email")
            
            if username != request.user.username:
                if not request.user.__class__.objects.filter(username=username).exists():
                    request.user.username = username
                    messages.success(request, "Username updated successfully!")
                else:
                    messages.error(request, "Username already taken.")
                    
            if email != request.user.email:
                if not request.user.__class__.objects.filter(email=email).exists():
                    request.user.email = email
                    messages.success(request, "Email updated successfully!")
                else:
                    messages.error(request, "Email already registered.")
                    
            request.user.save()
            
        elif "change_password" in request.POST:
            # Handle password change
            current_password = request.POST.get("current_password")
            new_password = request.POST.get("new_password")
            confirm_password = request.POST.get("confirm_password")
            
            if not request.user.check_password(current_password):
                messages.error(request, "Current password is incorrect.")
            elif new_password != confirm_password:
                messages.error(request, "New passwords do not match.")
            else:
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user)  # Keep user logged in
                messages.success(request, "Password changed successfully!")
                
        elif "update_team" in request.POST:
            # Handle favorite team update
            favorite_team_id = request.POST.get("favorite_team")
            if favorite_team_id:
                try:
                    # Get the team from our database
                    team = Team.objects.get(id=favorite_team_id)
                    
                    # Fetch teams from the API to get the correct ID
                    API_URL = "https://api.football-data.org/v4/competitions/PPL/teams"
                    HEADERS = {"X-Auth-Token": settings.FOOTBALL_API_KEY}
                    response = requests.get(API_URL, headers=HEADERS)
                    response.raise_for_status()
                    api_teams = response.json().get('teams', [])
                    
                    # Find the matching team in the API response
                    api_team = next((t for t in api_teams if t['name'] == team.name), None)
                    
                    if api_team:
                        # Update the team's ID and crest in database
                        team.id = api_team['id']
                        team.save()
                        
                        # Update the user's profile with the new team
                        profile.favorite_team = team
                        profile.save()
                        messages.success(request, "Favourite team updated successfully!")
                    else:
                        messages.error(request, "Could not find team in API.")
                except Team.DoesNotExist:
                    messages.error(request, "Invalid team selected.")
                except requests.exceptions.RequestException:
                    messages.error(request, "Could not connect to football API.")
            else:
                profile.favorite_team = None
                profile.save()
                messages.success(request, "Favourite team removed successfully!")
                
        return redirect("accounts:profile")

    # Get all teams for the favourite team selector
    teams = Team.objects.all()
    
    # Get user's prediction stats
    user_votes = PollVote.objects.filter(user=request.user).select_related('poll')
    total_votes = user_votes.count()
    correct_votes = user_votes.filter(is_correct=True).count()
    accuracy_percentage = (correct_votes / total_votes * 100) if total_votes > 0 else 0
    
    # Get pending and completed predictions
    pending_predictions = user_votes.filter(
        poll__is_closed=False
    ).order_by('poll__match_date')
    
    completed_predictions = user_votes.filter(
        poll__is_closed=True
    ).order_by('-poll__match_date')

    # Get quiz scores
    quiz_scores = {
        'regular': QuizScore.objects.filter(user=request.user, mode='regular').first(),
        'hard': QuizScore.objects.filter(user=request.user, mode='hard').first()
    }
    
    return render(request, "accounts/profile.html", {
        "profile": profile,
        "teams": teams,
        "total_votes": total_votes,
        "correct_votes": correct_votes,
        "accuracy_percentage": round(accuracy_percentage, 1),
        "pending_predictions": pending_predictions,
        "completed_predictions": completed_predictions,
        "quiz_scores": quiz_scores,
    })