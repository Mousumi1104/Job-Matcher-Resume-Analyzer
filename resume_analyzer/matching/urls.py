from django.urls import path
from django.contrib.auth import views as auth_views

from . import views
urlpatterns = [
    path('match-resume', views.compute_matches_for_resume, name="compute_matches_for_resume")
]