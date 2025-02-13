from django.urls import path
from .views import quiz, prediction_polls

app_name = "games"

urlpatterns = [
    path("quiz/", quiz, name="quiz"),
    path("polls/", prediction_polls, name="prediction_polls"),
]
