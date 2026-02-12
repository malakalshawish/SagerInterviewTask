# Sager Interview Task – Drone Telemetry Backend

Backend service for ingesting, storing, and querying drone telemetry data via **REST API** and **MQTT**.

Built with **Django + Django REST Framework**, **PostgreSQL**, **Docker**, and deployed on **Railway**.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Architecture](#architecture)
- [Environment Variables](#environment-variables)
- [Run Locally (No Docker)](#run-locally-no-docker)
- [Run with Docker](#run-with-docker)
- [MQTT Ingestion](#mqtt-ingestion)
- [API Documentation](#api-documentation)
- [REST API Endpoints](#rest-api-endpoints)
- [Authentication (JWT)](#authentication-jwt)
- [RBAC Rules](#rbac-rules)
- [Geofencing (No-Fly Zones)](#geofencing-no-fly-zones)
- [Tests](#tests)
- [Deployment to Railway](#deployment-to-railway)
- [Docker Notes & Troubleshooting](#docker-notes--troubleshooting)

---

## Features

### Telemetry ingestion
- REST endpoint: `POST /api/telemetry/`
- MQTT subscriber (background worker via Django management command)
- **Shared ingestion logic**: REST + MQTT both delegate to `drones/services.py::ingest_telemetry()`

### Drone management
- List all drones
- List online drones (last seen within 30s)
- List dangerous drones
- Find nearby drones (within 5 km)
- Mark a drone safe (**staff only**)

### Telemetry history
- Per-drone telemetry list
- GeoJSON flight path endpoint

### Danger classification (Strategy Pattern)
- Altitude rule (**> 500m**)
- Speed rule (**> 10 m/s**)
- Geofence rule (no-fly zones)
- Extensible rule system (add rules without rewriting ingestion)

### Geofencing (RBAC-managed)
- Prefer zones from DB (`GeofenceZone`), manageable by staff
- Fallback to zones from settings if DB empty
- Drone becomes dangerous if it enters a no-fly zone

### Security & production readiness
- JWT Authentication (SimpleJWT)
- API protected globally (expects `Authorization: Bearer <token>`)
- RBAC for staff-only actions
- Works with Railway HTTPS domain
- DB SSL support (Railway) + non-SSL local/dev support

### Documentation & tests
- OpenAPI schema: `/api/schema/`
- Swagger UI: `/api/docs/`
- Automated tests (REST integration + unit tests + RBAC + geofencing)

---

## Tech Stack

- Django
- Django REST Framework
- SimpleJWT
- PostgreSQL
- Gunicorn
- Docker + Docker Compose
- Railway (deployment)
- Mosquitto (MQTT broker for local testing)

---

## Project Structure
src/
├── cfehome/                # Project config + URLs + settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── drones/                 # Main app
│   ├── models.py
│   ├── serializers.py
│   ├── services.py         # Shared business logic (REST + MQTT)
│   ├── danger_strategies.py
│   ├── views.py
│   ├── urls.py
│   ├── utils.py
│   └── management/
│       └── commands/
│           └── run_mqtt.py  # MQTT subscriber command
│
└── manage.py

boot/
└── docker-run.sh           # Container boot script

Dockerfile
docker-compose.yml
requirements.txt
README.md
---

## Architecture

The system is designed so that **validation and business logic are reusable** across transports (REST + MQTT).

### High-level flow
      ┌──────────────┐
      │   REST API    │
      │  (HTTP POST)  │
      └──────┬────────┘
             │
             ▼
    ┌───────────────────────┐
    │ TelemetryInSerializer  │
    │  (Validation/Parsing)  │
    └──────────┬────────────┘
               │ validated_data
               ▼
    ┌───────────────────────┐
    │     Service Layer      │
    │   ingest_telemetry()   │
    └──────────┬────────────┘
               │
               ▼
    ┌───────────────────────┐
    │  Danger Classifier     │
    │ (Strategy Pattern)     │
    └──────────┬────────────┘
               │
               ▼
    ┌───────────────────────┐
    │     PostgreSQL DB      │
    │ Drone / DroneTelemetry │
    └───────────────────────┘


      ┌──────────────┐
      │     MQTT      │
      │  Subscriber   │
      └──────┬────────┘
             │ JSON payload
             ▼
    ┌───────────────────────┐
    │ TelemetryInSerializer  │
    │  (Same validation)     │
    └──────────┬────────────┘
               │ validated_data
               ▼
    ┌───────────────────────┐
    │     Service Layer      │
    │   ingest_telemetry()   │
    └───────────────────────┘

### Key design decisions
- **Service Layer** (`services.py`) isolates ingestion and state updates
- **Strategy Pattern** (`danger_strategies.py`) isolates danger rules
- **Thin Controllers**: views only validate → call service → return response
- **Same serializer** for REST + MQTT validation for consistent behavior

---

## Environment Variables

Create a `.env` file in the **project root**:


### `.env` example (local / docker)

```env
# Django
DJANGO_SECRET_KEY=dev-secret-key-change-me
DJANGO_DEBUG=1

# Database
DATABASE_URL=postgres://postgres:postgres@localhost:5432/postgres?sslmode=disable
DB_SSL_REQUIRE=0

# Optional security toggles (dev)
SECURE_HSTS_SECONDS=0

# MQTT
MQTT_HOST=localhost
MQTT_PORT=1883
MQTT_TOPIC=drones/telemetry
MQTT_USERNAME=
MQTT_PASSWORD=

SSL note 
	•	Local/Docker Postgres commonly does NOT support SSL → use sslmode=disable and DB_SSL_REQUIRE=0
	•	Railway Postgres typically requires SSL → set DB_SSL_REQUIRE=1 and use Railway-provided DATABASE_URL

---

Run Locally (No Docker)

0) Prerequisites
	•	Python 3.12+ recommended
	•	PostgreSQL running locally (or remote Postgres URL)
	•	Mosquitto for MQTT testing

1) Clone the repo
    git clone https://github.com/malakalshawish/SagerInterviewTask
    cd SagerInterviewTask

2) Create and activate virtualenv
```bash
    python -m venv venv
    source venv/bin/activate
```

3) Install dependencies
```bash
    pip install -r requirements.txt
```

4) Create .env
    DJANGO_SECRET_KEY=dev-secret-key-change-me
    DJANGO_DEBUG=1
    DATABASE_URL=postgres://postgres:postgres@localhost:5432/postgres?sslmode=disable
    DB_SSL_REQUIRE=0

    MQTT_HOST=localhost
    MQTT_PORT=1883
    MQTT_TOPIC=drones/telemetry
    MQTT_USERNAME=
    MQTT_PASSWORD=

5) Run migrations
```bash
    cd src
    python manage.py migrate
```

6) Create superuser
```bash
    python manage.py createsuperuser
```

7) Run the server
```bash
    python manage.py runserver 0.0.0.0:8000
```
•	API base: http://127.0.0.1:8000/api/
•	Swagger UI: http://127.0.0.1:8000/api/docs/

---

Run with Docker

0) Prerequisites
	•	Docker Desktop (Mac/Windows) or Docker Engine + Compose (Linux)

1) Build + start containers
    From project root:
    ```bash
        docker compose up -d --build
    ```
Verify:
```bash
    docker compose ps
```
Expected:
	•	db is healthy
	•	web is running

2) Access API

This setup maps container 8000 → host 8001:
	•	API base: http://127.0.0.1:8001/api/
	•	Swagger UI: http://127.0.0.1:8001/api/docs/

3) Create superuser inside Docker
```bash
    docker compose exec web sh
```
Inside container:
```bash
    /opt/venv/bin/python manage.py createsuperuser
    exit
```
---

## MQTT Ingestion

The project can ingest telemetry via MQTT using the `run_mqtt` management command.

### Topic format (per task)

Telemetry is published to:

- `thing/product/{drone_serial}/osd`

To subscribe to all drones, use:

- `thing/product/+/osd`

### Run MQTT ingestion with Docker (recommended)

This repo includes a Mosquitto broker in `docker-compose.yml`, so you don’t need to install a broker locally.

1) Start the stack:

```bash
docker compose up -d --build
```
2)	Apply migrations:
```bash
    docker compose exec web /opt/venv/bin/python manage.py migrate
```
3)	Run the MQTT subscriber (keep this terminal open):
```bash
    docker compose exec web /opt/venv/bin/python manage.py run_mqtt
```
You should see something like:
	•	Connected to MQTT broker ...
	•	Subscribed to topic: thing/product/+/osd

	4.	Publish a test message (new terminal)

If you have mosquitto_pub installed:
```bash
    mosquitto_pub -h localhost -p 1883 -t "thing/product/DR-001/osd" -m '{"lat":37.7749,"lng":-122.4194,"speed":12.3,"timestamp":"2026-01-01T12:00:00Z"}'
```
The subscriber extracts serial from the topic if it’s not present in the payload.

5)	Verify ingestion

Verify via Django shell:
```bash
    docker compose exec web /opt/venv/bin/python manage.py shell -c "
from drones.models import DroneTelemetry
print('Telemetry count:', DroneTelemetry.objects.count())
print(list(DroneTelemetry.objects.order_by('-id').values('id','drone_id','lat','lng','height_m','horizontal_speed_mps','timestamp')[:5]))
"
```
### Run MQTT ingestion locally (no Docker web)

You can still use Docker for DB + broker, while running Django locally:
1)	Start services:
```bash
    docker compose up -d db mosquitto
```
2)	Set .env for local Django (example):
```bash
    DATABASE_URL=postgres://postgres:postgres@localhost:5432/postgres
    MQTT_HOST=localhost
    MQTT_PORT=1883
    MQTT_TOPIC=thing/product/+/osd
    DJANGO_DEBUG=1
    DJANGO_SECRET_KEY=dev-secret-key-change-me
```
3)	Run Django migrations and MQTT subscriber:
```bash
    cd src
    python manage.py migrate
    python manage.py run_mqtt
```
4)	Publish a test message:
```bash
    mosquitto_pub -h localhost -p 1883 -t "thing/product/DR-001/osd" -m '{"lat":37.7749,"lng":-122.4194,"speed":12.3,"timestamp":"2026-01-01T12:00:00Z"}'
```

How it works
	•	MQTT message → TelemetryInSerializer validates + parses
	•	Calls services.ingest_telemetry(validated_data)
	•	Creates telemetry, updates drone state + danger classification

⸻

API Documentation
	•	OpenAPI schema: /api/schema/
	•	Swagger UI: /api/docs/

⸻

REST API Endpoints
| Method | Endpoint                                   | Description           |
|--------|--------------------------------------------|-----------------------|
| POST   | `/api/telemetry/`                          | Ingest telemetry      |
| GET    | `/api/drones/`                             | List drones           |
| GET    | `/api/drones/online/`                      | Online drones         |
| GET    | `/api/drones/dangerous/`                   | Dangerous drones      |
| GET    | `/api/drones/nearby/?lat=&lng=`            | Nearby drones         |
| GET    | `/api/drones/{serial}/telemetry/`          | Telemetry history     |
| GET    | `/api/drones/{serial}/path/`               | GeoJSON flight path   |
| POST   | `/api/drones/{serial}/mark-safe/`          | Staff only            |
| GET    | `/api/geofences/`                          | List geofences        |
| POST   | `/api/geofences/`                          | Staff only            |
| PUT    | `/api/geofences/{id}/`                     | Staff only            |
| DELETE | `/api/geofences/{id}/`                     | Staff only            |


⸻

Authentication (JWT)

1) Obtain tokens

POST /api/token/

Example (local):
```bash
    curl -i -X POST http://127.0.0.1:8000/api/token/ \
    -H "Content-Type: application/json" \
    -d '{"username":"<USER>","password":"<PASS>"}'
```
Example (docker):
```bash
    curl -i -X POST http://127.0.0.1:8001/api/token/ \
    -H "Content-Type: application/json" \
    -d '{"username":"<USER>","password":"<PASS>"}'
```
2) Use access token
```bash
    curl -i http://127.0.0.1:8000/api/drones/ \
    -H "Authorization: Bearer <ACCESS_TOKEN>"
```
3) Refresh token
```bash
    POST /api/token/refresh/
```

⸻

RBAC Rules

Regular authenticated users (is_staff = False)

Allowed to:
	•	View drones and telemetry
	•	Ingest telemetry
	•	View nearby / online / dangerous drones
	•	View geofence zones

Not allowed to:
	•	Create, update, or delete geofence zones
	•	Mark drones as safe

Staff users (is_staff = True)

Allowed to:
	•	All regular user actions
	•	Create / update / delete geofence zones
	•	Mark drones as safe

RBAC-Protected Endpoints

### Geofence Management

| Endpoint                    | Method | Access        |
|----------------------------|--------|---------------|
| `/api/geofences/`          | GET    | Authenticated |
| `/api/geofences/`          | POST   | Staff only    |
| `/api/geofences/{id}/`     | PUT    | Staff only    |
| `/api/geofences/{id}/`     | DELETE | Staff only    |

### Drone Safety Override

| Endpoint                               | Method | Access     |
|----------------------------------------|--------|------------|
| `/api/drones/{serial}/mark-safe/`     | POST   | Staff only |


⸻

Geofencing (No-Fly Zones)

A drone is marked dangerous if it enters any defined geofence,
even if altitude and speed are within safe limits.

Configuration

Geofences are resolved in this order:
	1.	Database zones (RBAC-managed)
	2.	Settings fallback:
	•	DRONE_GEOFENCE_ZONES
	•	or NO_FLY_ZONES

Example settings structure:
```bash
    DRONE_GEOFENCE_ZONES = 
    [
    {"name": "Airport Zone", "lat": 31.9500, "lng": 35.9100, "radius_km": 1.0}
    ]
```

⸻

Tests

Local:
```bash
    cd src
    python manage.py test -v 2
```
Docker:
```bash
    docker compose exec web /opt/venv/bin/python manage.py test -v 2
```

⸻

Deployment to Railway

This project runs best on Railway as **two services**:

1) **Web/API service** (Gunicorn) — serves REST endpoints
2) **MQTT Worker service** (`python manage.py run_mqtt`) — ingests MQTT telemetry into Postgres

0) Prerequisites
	•	Railway account
	•	GitHub repo with this project pushed

1) Push code
```bash
    git add .
    git commit -m "Deploy to Railway"
    git push
```
2) Create project on Railway
	•	Create new Railway project
	•	Connect GitHub repository
	•	Add PostgreSQL service

3) Set environment variables (Railway)

On the Django service:

Required:
	•	DJANGO_SECRET_KEY=<strong production key>
	•	DJANGO_DEBUG=0
	•	DB_SSL_REQUIRE=1

Railway provides:
	•	DATABASE_URL (use it)

if you run MQTT worker on Railway too:
	•	MQTT_HOST
	•	MQTT_PORT
	•	MQTT_TOPIC
	•	MQTT_USERNAME
	•	MQTT_PASSWORD

4) Start command / process

Typical web start command:
```bash
    gunicorn cfehome.wsgi:application --bind 0.0.0.0:$PORT
```
If you use a boot script, ensure it runs:
```bash
	•	python manage.py migrate
	•	python manage.py collectstatic --noinput
	•	gunicorn ...
```
After deployment, publish a test message to your broker:

```bash
mosquitto_pub -h <MQTT_HOST> -p 1883 -t "thing/product/DR-RAILWAY-001/osd" -m '{"serial":"DR-RAILWAY-001","lat":37.7749,"lng":-122.4194,"speed":12.3,"timestamp":"2026-01-01T12:00:00Z"}'
```
5) Verify
	•	Open the Railway URL
	•	Visit /api/docs/
	•	Test /api/token/ and /api/drones/

⸻

Docker Notes & Troubleshooting

1) “connection to server at 127.0.0.1:5432 failed” inside Docker

Inside containers, localhost points to the container itself — not the db service.

Correct:
```bash
    postgres://postgres:postgres@db:5432/postgres
```
Incorrect:
```bash
    postgres://postgres:postgres@localhost:5432/postgres
```
2) Web container exits immediately
Check logs:
```bash
docker compose logs --tail=200 web
```
Check:
```bash
    docker compose logs --tail=200 web
```
Rebuild clean:
```bash
    docker compose down
    docker compose up -d --build
```
3) SSL vs non-SSL Postgres

Local Docker Postgres is usually non-SSL.
Railway Postgres usually requires SSL.

Local/Docker:
	•	DB_SSL_REQUIRE=0
	•	DATABASE_URL=...sslmode=disable

Railway:
	•	DB_SSL_REQUIRE=1
	•	use Railway-provided DATABASE_URL

4) Django not found inside container

If you see:
    ModuleNotFoundError: No module named 'django'
Use the venv Python inside container:
```bash
    docker compose exec web /opt/venv/bin/python manage.py <command>
```
Example:
```bash
    docker compose exec web /opt/venv/bin/python manage.py createsuperuser
```

5) Port already in use (8000)

If local runserver says:
    Error: That port is already in use.
Check:
```bash
    lsof -i :8000
```
Or run on another port:
```bash
    python manage.py runserver 0.0.0.0:8002
```
6) Danger rules not triggering

If drone remains:
```bash
    "is_dangerous": false
```
Make sure your payload uses:
```bash
    {
    "height_m": 600,
    "horizontal_speed_mps": 12
    }
```
7) Railway 502 Error

If Railway shows 502 but logs show Gunicorn running:

Check:
	•	DATABASE_URL exists in Railway variables
	•	DB_SSL_REQUIRE=1
	•	DJANGO_DEBUG=0
	•	$PORT is used in gunicorn bind:
        ```bash
            gunicorn cfehome.wsgi:application --bind 0.0.0.0:$PORT
        ```
