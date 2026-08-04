from django.urls import path
from . import health_views

urlpatterns = [
    path("", health_views.shallow_health, name="health-shallow"),
    path("ready/", health_views.deep_health, name="health-ready"),
]
