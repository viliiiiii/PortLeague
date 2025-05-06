from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("all-fixtures/", views.all_fixtures, name="all_fixtures"),
    path("games/", views.games, name="games"),
]