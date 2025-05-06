from django.urls import path
from . import views

app_name = "games"

urlpatterns = [
    path("quiz/", views.quiz, name="quiz"),  # Quiz selection page
    path("predictions/", views.prediction_polls, name="prediction_polls"),
]
