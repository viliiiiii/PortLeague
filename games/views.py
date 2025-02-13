from django.shortcuts import render, redirect
from .models import QuizQuestion
from .forms import QuizForm
import random

# Create your views here.

def prediction_polls(request):
    return render(request, "games/prediction_polls.html")

def quiz(request):
    # Get a random question
    question = QuizQuestion.objects.order_by("?").first()

    if not question:
        return render(request, "games/quiz.html", {"error": "No questions available."})

    form = QuizForm(request.POST or None)
    result = None
    # Check answer
    if request.method == "POST":
        selected_answer = request.POST.get("answer")
        correct_answer_text = None

        # Match the correct answer with the team name
        if question.correct_answer == "A":
            correct_answer_text = question.option_a
        elif question.correct_answer == "B":
            correct_answer_text = question.option_b
        elif question.correct_answer == "C":
            correct_answer_text = question.option_c
        elif question.correct_answer == "D":
            correct_answer_text = question.option_d

        if selected_answer == question.correct_answer:
            result = "Correct!"
        else:
            result = f"Wrong! The correct answer was {correct_answer_text}."

    return render(request, "games/quiz.html", {
        "question": question,
        "form": form,
        "result": result
    })
