import json
import os
from datetime import datetime, timezone as dt_timezone

from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import SensorReading


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
