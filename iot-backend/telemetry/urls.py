from django.urls import path

from .views import health, ingest_reading

urlpatterns = [
    path("health/", health, name="health"),
    path("readings/", ingest_reading, name="ingest-reading"),
]
