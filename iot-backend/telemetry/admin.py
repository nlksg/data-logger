from django.contrib import admin

from .models import SensorReading


@admin.register(SensorReading)
class SensorReadingAdmin(admin.ModelAdmin):
    list_display = ("id", "device_id", "humidity", "temperature", "sensor_timestamp", "created_at")
    list_filter = ("device_id", "created_at")
    search_fields = ("device_id",)
    ordering = ("-created_at",)
