from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("all-fixtures/", views.all_fixtures, name="all_fixtures"),
]