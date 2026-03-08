from django.urls import path

from .views import dashboard, health, ingest_reading, list_readings

urlpatterns = [
    path("health/", health, name="health"),
    path("readings/", ingest_reading, name="ingest-reading"),
    path("readings/list/", list_readings, name="list-readings"),
    path("dashboard/", dashboard, name="dashboard"),
]
