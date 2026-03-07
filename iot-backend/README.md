# iot-backend

Django + PostgreSQL backend for receiving sensor data from Raspberry Pi.

## API
- Health check: `GET /api/v1/health/`
- Ingest reading: `POST /api/v1/readings/`

Example payload:
```json
{
  "device_id": "1",
  "humidity": 45.2,
  "temperature": 27.1,
  "timestamp": "2026-03-06T10:00:00Z"
}
```

Header (recommended):
- `X-API-Token: <SENSOR_API_TOKEN>`

## Setup (GCE VM)
1. `python3 -m venv .venv`
2. `. .venv/bin/activate`
3. `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and set real values.
5. Export env vars from `.env`.
6. Run migrations:
   - `python manage.py makemigrations`
   - `python manage.py migrate`
7. Start server:
   - Dev: `python manage.py runserver 0.0.0.0:8000`
   - Prod: `gunicorn iot_backend.wsgi:application --bind 0.0.0.0:8000`

## Raspberry Pi sender
The root-level `sensor_read.py` now posts readings to the backend.

Set on Raspberry Pi before running:
- `IOT_API_URL` (example: `http://<GCE_VM_IP>:8000/api/v1/readings/`)
- `IOT_API_TOKEN` (must match backend `SENSOR_API_TOKEN`)

## Git + GitHub Actions setup
From `/home/nlksg/iot-backend`:

```bash
git init
git branch -M main
git add .
git commit -m "Initial iot-backend scaffold"
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

CI workflow file is already added at `.github/workflows/ci.yml`.

After push:
1. Open GitHub repo -> Actions tab.
2. Confirm `CI` workflow ran successfully on `main`.
3. For pull requests, the same checks run automatically.

## Forced Deployment