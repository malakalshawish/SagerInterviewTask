# Sager Interview Task – Drone Telemetry Backend

Backend service for ingesting, storing, and querying drone telemetry data via **REST API** and **MQTT**.

Built with **Django + Django REST Framework**, PostgreSQL, and MQTT.

---

## Features

- 📡 **Telemetry ingestion**
  - REST endpoint (`POST /api/telemetry/`)
  - MQTT subscriber (background worker)
- 🛩 **Drone management**
  - List all drones
  - List online drones (last seen within 30s)
  - List dangerous drones
  - Find nearby drones (within 5 km)
- 📍 **Telemetry history**
  - Per-drone telemetry list
  - GeoJSON flight path
- 📖 **OpenAPI / Swagger docs**
- 🧪 **Automated tests**

---

## Tech Stack

- Python 3
- Django
- Django REST Framework
- PostgreSQL
- MQTT (Mosquitto / paho-mqtt)
- drf-spectacular (OpenAPI)

---

## Project Structure

```
src/
├── cfehome/                # Project config + schema/docs
├── drones/                 # Main app
│   ├── models.py
│   ├── serializers.py
│   ├── services.py         # Shared business logic (REST + MQTT)
│   ├── views.py
│   ├── urls.py
│   └── management/
│       └── commands/
│           └── run_mqtt.py # MQTT subscriber command
└── manage.py
```

---

## Environment Variables

Create a `.env` file:

```env
# Django
DEBUG=True
SECRET_KEY=your-secret-key

# Database (Railway / local Postgres)
DATABASE_URL=postgresql://...

# MQTT
MQTT_HOST=localhost
MQTT_PORT=1883
MQTT_TOPIC=drones/telemetry
MQTT_USERNAME=
MQTT_PASSWORD=
```

---

## Setup

### 1️⃣ Create virtual environment & install dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2️⃣ Run migrations

```bash
python manage.py migrate
```

### 3️⃣ Run server

```bash
python manage.py runserver
```

---

## API Documentation

- OpenAPI schema: `/api/schema/`
- Swagger UI: `/api/docs/`

---

## REST API Endpoints

| Method | Endpoint | Description |
|------|--------|------------|
| POST | `/api/telemetry/` | Ingest telemetry |
| GET | `/api/drones/` | List drones |
| GET | `/api/drones/online/` | Online drones |
| GET | `/api/drones/dangerous/` | Dangerous drones |
| GET | `/api/drones/nearby/?lat=&lng=` | Nearby drones |
| GET | `/api/drones/{serial}/telemetry/` | Telemetry history |
| GET | `/api/drones/{serial}/path/geojson/` | GeoJSON flight path |

---

## MQTT Ingestion

### Run MQTT subscriber

```bash
python manage.py run_mqtt \
  --host localhost \
  --port 1883 \
  --topic drones/telemetry
```

### Example publish

```bash
mosquitto_pub -h localhost -p 1883 -t drones/telemetry \
  -m '{"serial":"DRONE_1","lat":31.95,"lng":35.91,"height_m":600,"horizontal_speed_mps":12}'
```

### How it works

- MQTT message → `TelemetryInSerializer` (validation)
- Shared logic → `services.ingest_telemetry()`
- Telemetry + drone state saved to DB

---

## Tests

Run all tests:

```bash
python manage.py test
```

---

## Design Notes

- Service layer (`services.py`) isolates business logic
- REST and MQTT share ingestion logic
- Environment-driven configuration
- Clean separation of concerns

---

## Deployment Notes

- Uses PostgreSQL (Railway compatible)
- MQTT subscriber runs as a separate process:
  ```bash
  python manage.py run_mqtt
  ```
