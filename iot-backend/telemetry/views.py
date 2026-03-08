import json
import os
from datetime import date, datetime, time, timedelta, timezone as dt_timezone
from zoneinfo import ZoneInfo

from django.db.models import DateTimeField
from django.db.models.functions import Coalesce
from django.http import HttpRequest, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import SensorReading

YANGON_TIMEZONE = ZoneInfo("Asia/Yangon")


def _get_client_ip(request: HttpRequest) -> str | None:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _parse_iso_datetime(value: str | None):
    if not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, dt_timezone.utc)
    return parsed


@csrf_exempt
@require_http_methods(["GET"])
def health(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok"})


@csrf_exempt
@require_http_methods(["GET"])
def list_readings(request: HttpRequest) -> JsonResponse:
    start_date_param = request.GET.get("start_date")
    end_date_param = request.GET.get("end_date")

    try:
        start_date = date.fromisoformat(start_date_param) if start_date_param else None
        end_date = date.fromisoformat(end_date_param) if end_date_param else None
    except ValueError:
        return JsonResponse(
            {"error": "start_date and end_date must be in YYYY-MM-DD format"},
            status=400,
        )

    if start_date and end_date and end_date < start_date:
        return JsonResponse(
            {"error": "end_date must be the same as or after start_date"},
            status=400,
        )

    readings = SensorReading.objects.annotate(
        effective_timestamp=Coalesce(
            "sensor_timestamp",
            "created_at",
            output_field=DateTimeField(),
        )
    )

    if start_date:
        start_dt = timezone.make_aware(
            datetime.combine(start_date, time.min),
            YANGON_TIMEZONE,
        )
        readings = readings.filter(effective_timestamp__gte=start_dt)

    if end_date:
        end_exclusive_dt = timezone.make_aware(
            datetime.combine(end_date + timedelta(days=1), time.min),
            YANGON_TIMEZONE,
        )
        readings = readings.filter(effective_timestamp__lt=end_exclusive_dt)

    readings = readings.order_by("-effective_timestamp", "-id")[:2000]
    data = [
        {
            "id": reading.id,
            "device_id": reading.device_id,
            "humidity": float(reading.humidity),
            "temperature": float(reading.temperature),
            "timestamp": reading.effective_timestamp.isoformat(),
            "created_at": reading.created_at.isoformat(),
        }
        for reading in readings
    ]
    data.reverse()
    return JsonResponse(
        {
            "readings": data,
            "filters": {
                "start_date": start_date_param,
                "end_date": end_date_param,
            },
        }
    )


@require_http_methods(["GET"])
def dashboard(request: HttpRequest):
    return render(request, "telemetry/dashboard.html")


@csrf_exempt
@require_http_methods(["POST"])
def ingest_reading(request: HttpRequest) -> JsonResponse:
    expected_token = os.getenv("SENSOR_API_TOKEN", "")
    provided_token = request.headers.get("X-API-Token", "")
    if expected_token and provided_token != expected_token:
        return JsonResponse({"error": "unauthorized"}, status=401)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"error": "invalid JSON"}, status=400)

    device_id = payload.get("device_id")
    humidity = payload.get("humidity")
    temperature = payload.get("temperature")
    sensor_timestamp = payload.get("timestamp")

    if not device_id or humidity is None or temperature is None:
        return JsonResponse(
            {"error": "device_id, humidity, and temperature are required"},
            status=400,
        )

    try:
        reading = SensorReading.objects.create(
            device_id=str(device_id),
            humidity=humidity,
            temperature=temperature,
            sensor_timestamp=_parse_iso_datetime(sensor_timestamp),
            source_ip=_get_client_ip(request),
        )
    except (TypeError, ValueError):
        return JsonResponse({"error": "invalid payload values"}, status=400)

    return JsonResponse(
        {
            "id": reading.id,
            "device_id": reading.device_id,
            "humidity": float(reading.humidity),
            "temperature": float(reading.temperature),
            "created_at": reading.created_at.isoformat(),
        },
        status=201,
    )
