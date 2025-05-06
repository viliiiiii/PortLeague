from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.db import IntegrityError, models, transaction
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from .models import (
    QuizQuestion, MatchPoll, PollVote, QuizScore,
    # Removed QuizAttempt, QuestionResponse
)
from .forms import QuizForm
from core.models import Team
import requests
from datetime import datetime, timedelta, timezone as dt_timezone
import random
import json
import os
from django.urls import reverse
from django.db.models import Avg, Count, Q
from accounts.models import UserStatistics

# Create your views here.

def create_or_update_polls():
    """Fetch upcoming matches and create polls with them"""
    API_URL = "https://api.football-data.org/v4/competitions/PPL/matches"
    HEADERS = {"X-Auth-Token": settings.FOOTBALL_API_KEY}
    
    try:
        response = requests.get(API_URL, headers=HEADERS)
        response.raise_for_status()
        matches = response.json().get("matches", [])
        
        # Only create polls for upcoming matches in the next 7 days
        now = timezone.now()
        week_later = now + timedelta(days=7)
        
        for match in matches:
            match_date = datetime.strptime(match["utcDate"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt_timezone.utc)
            
            # Skip if match is in the past or more than a week away
            if match_date < now or match_date > week_later:
                continue
                
            # Create or update poll
            poll, created = MatchPoll.objects.get_or_create(
                match_id=match["id"],
                defaults={
                    'home_team': match["homeTeam"]["name"],
                    'away_team': match["awayTeam"]["name"],
                    'match_date': match_date,
                }
            )
            
            # Update crests even if poll exists
            poll.home_team_crest = match["homeTeam"]["crest"]
            poll.away_team_crest = match["awayTeam"]["crest"]
            poll.save()
            
        # Update results for finished matches
        update_poll_results()
            
    except requests.exceptions.RequestException as e:
        print(f"Error fetching matches: {e}")

def update_poll_results():
    """Update results for finished matches"""
    # Get all unclosed polls for matches that have ended
    unclosed_polls = MatchPoll.objects.filter(
        is_closed=False,
        match_date__lt=timezone.now()
    )
    
    if not unclosed_polls:
        return
        
    API_URL = "https://api.football-data.org/v4/competitions/PPL/matches"
    HEADERS = {"X-Auth-Token": settings.FOOTBALL_API_KEY}
    
    try:
        response = requests.get(API_URL, headers=HEADERS)
        response.raise_for_status()
        matches = {match["id"]: match for match in response.json().get("matches", [])}
        
        for poll in unclosed_polls:
            match = matches.get(poll.match_id)
            if not match or match["status"] != "FINISHED":
                continue
                
            # Determine the winner
            home_score = match["score"]["fullTime"]["home"]
            away_score = match["score"]["fullTime"]["away"]
            
            if home_score > away_score:
                outcome = "HOME"
            elif away_score > home_score:
                outcome = "AWAY"
            else:
                outcome = "DRAW"
                
            # Update poll and votes
            poll.correct_outcome = outcome
            poll.is_closed = True
            poll.save()
            
            # Update vote accuracy
            PollVote.objects.filter(poll=poll).update(
                is_correct=(models.Q(prediction=outcome))
            )
            
    except requests.exceptions.RequestException as e:
        print(f"Error updating poll results: {e}")

def prediction_polls(request):
    """
    Main view for prediction polls.
    """
    # Create/update polls from upcoming matches
    create_or_update_polls()
    
    # Get open polls (future matches only)
    open_polls = MatchPoll.objects.filter(
        is_closed=False,
        match_date__gt=timezone.now()
    ).order_by('match_date')
    
    # Get voted polls (future matches only)
    voted_polls = MatchPoll.objects.filter(
        is_closed=False,
        match_date__gt=timezone.now(),
        votes__user=request.user if request.user.is_authenticated else None
    ).order_by('match_date')
    
    # Remove voted polls from open polls
    open_polls = open_polls.exclude(id__in=voted_polls.values_list('id', flat=True))
    
    # Get completed polls (past matches with results)
    completed_polls = MatchPoll.objects.filter(
        is_closed=True
    ).order_by('-match_date')
    
    # Get user's votes if authenticated
    user_votes = {}
    if request.user.is_authenticated:
        user_votes = {
            vote.poll_id: vote.prediction 
            for vote in PollVote.objects.filter(user=request.user)
        }
    
    # Add user_vote to each poll
    for poll in open_polls:
        poll.user_vote = user_votes.get(poll.id)
        poll.user_has_voted = poll.id in user_votes
    
    for poll in voted_polls:
        poll.user_vote = user_votes.get(poll.id)
        poll.user_has_voted = True
    
    for poll in completed_polls:
        poll.user_vote = user_votes.get(poll.id)
        poll.user_has_voted = poll.id in user_votes
    
    # Handle voting submission
    if request.method == "POST" and request.user.is_authenticated:
        poll_id = request.POST.get('poll_id')
        prediction = request.POST.get('prediction')
        
        if poll_id and prediction:
            try:
                poll = MatchPoll.objects.get(id=poll_id, is_closed=False)
                PollVote.objects.create(
                    poll=poll,
                    user=request.user,
                    prediction=prediction
                )
                messages.success(request, "Your prediction has been recorded!")
            except MatchPoll.DoesNotExist:
                messages.error(request, "This poll is no longer available.")
            except IntegrityError:
                # Triggered by unique_together constraint in PollVote model
                messages.error(request, "You have already voted on this match!")
        
        return redirect('games:prediction_polls')
    
    return render(request, "games/prediction_polls.html", {
        "open_polls": open_polls,
        "voted_polls": voted_polls,
        "completed_polls": completed_polls
    })


def quiz(request):
    """
    Quiz feature that handles both quiz selection and quiz modes.
    Randomly selects questions based on difficulty, processes user answers,
    and tracks high scores.
    """
    quiz_mode = request.GET.get('mode')
    if not quiz_mode:
        return render(request, "games/quiz_select.html")

    # Determine difficulty queryset and select random questions
    if quiz_mode == 'hard':
        questions_qs = QuizQuestion.objects.filter(difficulty='hard').order_by('?')[:10]
    else:
        questions_qs = QuizQuestion.objects.filter(difficulty__in=['easy', 'medium']).order_by('?')[:10]
    questions = list(questions_qs)

    if not questions:
        return render(request, "games/quiz.html", {
            "error": "No questions available.",
            "timed": quiz_mode == 'hard'
        })

    # Handle quiz submission
    if request.method == "POST":
        correct_answers = 0
        total_questions = len(questions)
        for i, question in enumerate(questions):
            user_answer = request.POST.get(f'answer_{i}')
            is_correct = False
            if user_answer in ['0', '1', '2', '3']:
                # Convert numeric answer (0,1,2,3) to letter (A,B,C,D)
                is_correct = (chr(65+int(user_answer)) == question.correct_answer)
                if is_correct:
                    correct_answers += 1

        score = (correct_answers / total_questions) * 100
        
        # Save score if user is logged in and it's better than their previous best
        if request.user.is_authenticated:
            try:
                quiz_score = QuizScore.objects.get(user=request.user, mode=quiz_mode)
                if score > quiz_score.score:
                    quiz_score.score = score
                    quiz_score.save()
            except QuizScore.DoesNotExist:
                QuizScore.objects.create(
                    user=request.user,
                    mode=quiz_mode,
                    score=score
                )
        return render(request, "games/quiz_results.html", {
            "score": round(score, 1),
            "correct_answers": correct_answers,
            "total_questions": total_questions
        })

    # For GET, prepare choices for template
    questions_for_template = []
    for q in questions:
        questions_for_template.append({
            'question': q.question,
            'choices': [q.option_a, q.option_b, q.option_c, q.option_d]
        })
    return render(request, "games/quiz.html", {
        "questions": questions_for_template,
        "timed": quiz_mode == 'hard'
    })
