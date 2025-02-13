from django.urls import path
from .views import standings, team_details 

app_name = "standings"

urlpatterns = [
    path("", standings, name="standings"),
    path("team/<int:team_id>/", team_details, name="team_details"), 
]