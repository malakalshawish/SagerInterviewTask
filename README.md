# Sager Interview Task – Drone Telemetry Backend

Backend service for ingesting, storing, and querying drone telemetry data via **REST API** and **MQTT**.

Built with **Django + Django REST Framework**, PostgreSQL, and MQTT.

---

## Features

-**Telemetry ingestion**
  - REST endpoint (`POST /api/telemetry/`)
  - MQTT subscriber (background worker)
-**Drone management**
  - List all drones
  - List online drones (last seen within 30s)
  - List dangerous drones
  - Find nearby drones (within 5 km)
-**Telemetry history**
  - Per-drone telemetry list
  - GeoJSON flight path
-**OpenAPI / Swagger docs**
-**Automated tests**

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

### 1- Create virtual environment & install dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2- Run migrations

```bash
python manage.py migrate
```

### 3- Run server

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
## Root URL Redirect

By default, the application redirects the root URL (/) to the Django Admin interface.

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

## Design Patterns Used

This project intentionally applies multiple design patterns to ensure the system is modular, extensible, testable, and transport-agnostic.

---

### 1. Strategy Pattern (Primary)

The **Strategy Pattern** is used for dangerous-drone classification.

Each danger rule is implemented as an independent strategy (e.g. altitude rule, speed rule).  
A classifier context applies all configured strategies to incoming telemetry.

This allows new danger rules to be added without modifying telemetry ingestion logic.

**Implementation:**
- `drones/danger_strategies.py`
- Used by `ingest_telemetry()` in `drones/services.py`

**Why Strategy fits here:**
- Danger criteria are expected to evolve
- Rules must be swappable and extensible
- Avoids hard-coded conditional logic

---

### 2. Service Layer Pattern

A **Service Layer** encapsulates all core business logic related to telemetry ingestion.

Both REST and MQTT ingestion paths delegate to the same service function.

**Implementation:**
- `drones/services.py`
- `ingest_telemetry(validated_data)`

**Responsibilities:**
- Create telemetry records
- Update drone latest state
- Apply danger classification strategies

This prevents duplication and ensures consistent behavior across transports.

---

### 3. Thin Controller Pattern (Supporting)

API views act as thin controllers:

- Validate input
- Call service layer
- Return responses

They do not contain business rules.

**Benefits:**
- Improved readability
- Easier testing
- Clear separation of concerns

---

### 4. Command Pattern (Supporting)

The MQTT subscriber is implemented as a Django **management command**, following the Command Pattern.

**Example:**
```bash
python manage.py run_mqtt
```
---


## Architecture

The system is designed with a clear separation of concerns to support multiple ingestion methods (REST and MQTT) while avoiding duplicated logic.

### High-level flow

```
          ┌──────────────┐
          │   REST API   │
          │  (HTTP POST) │
          └──────┬───────┘
                 │
                 │ validated JSON
                 ▼
        ┌────────────────────┐
        │  TelemetryInSerializer │
        │  (input validation) │
        └─────────┬──────────┘
                  │ validated_data
                  ▼
        ┌────────────────────┐
        │   Service Layer    │
        │ ingest_telemetry() │
        │ (business logic)   │
        └─────────┬──────────┘
                  │
        ┌─────────▼──────────┐
        │    PostgreSQL DB   │
        │  Drone / Telemetry │
        └────────────────────┘


          ┌──────────────┐
          │     MQTT     │
          │   Subscriber │
          └──────┬───────┘
                 │ JSON payload
                 ▼
        ┌────────────────────┐
        │  TelemetryInSerializer │
        │  (same validation) │
        └─────────┬──────────┘
                  │ validated_data
                  ▼
        ┌────────────────────┐
        │   Service Layer    │
        │ ingest_telemetry() │
        │ (shared logic)     │
        └─────────┬──────────┘
                  │
        ┌─────────▼──────────┐
        │    PostgreSQL DB   │
        └────────────────────┘
```

### Key design decisions

- **Single source of truth for ingestion logic**  
  All telemetry processing (creation, danger classification, state updates) lives in `services.py`.

- **Transport-agnostic business logic**  
  The service layer does not depend on HTTP or MQTT, making it reusable and testable.

- **Serializer-driven validation**  
  Both REST and MQTT use the same `TelemetryInSerializer` to guarantee identical validation rules.

- **Process separation**  
  - REST API runs as a web process
  - MQTT subscriber runs as a background worker (`python manage.py run_mqtt`)

This architecture allows the system to scale ingestion sources without increasing complexity or duplicating code.

## Deployment Notes

- Uses PostgreSQL (Railway compatible)
- MQTT subscriber runs as a separate process:
  ```bash
  python manage.py run_mqtt
  ```

---

## Testing

This project includes both:
- **Feature/integration tests** for REST endpoints (validation, persistence, responses)
- **Unit tests** for core logic (Strategy Pattern classification + haversine distance)

Run:
```bash
python manage.py test -v 2
```

---
---
---
## Bonus

## Geofencing (No-Fly Zones)

The system supports geofencing using configurable no-fly zones.

A drone is marked dangerous if it enters any defined geofence —
even if altitude and speed are within safe limits.

Configuration

Geofences are defined in Django settings:
        DRONE_GEOFENCE_ZONES = [
        {
            "name": "Airport Zone",
            "lat": 31.9500,
            "lng": 35.9100,
            "radius_km": 1.0
        }
    ]
No database migrations are required since zones are configuration-driven.

Classification Logic

Geofencing is implemented as part of the Strategy Pattern:
	•	HeightRule → altitude violations
	•	SpeedRule → speed violations
	•	GeofenceClassifier → spatial violations

These strategies are combined using a Composite Classifier, allowing:
	•	Independent rules
	•	Easy extension (e.g. time-based or restricted-airspace rules)
	•	Clean separation of concerns

Resulting Behavior

If a drone enters a no-fly zone:
	•	is_dangerous = true
	•	A descriptive geofence reason is added:
        "Entered no-fly zone: Airport Zone"

Testing Coverage

Geofencing is fully tested at two levels:
	•	Unit tests: classifier behavior (inside vs outside zones)
	•	Feature tests: full API ingestion → danger flag persistence

This guarantees correctness both in isolation and end-to-end.


## Authentication (JWT)

This API uses JWT (JSON Web Tokens) for authentication and authorization.

Authentication is enforced globally via Django REST Framework settings:
	•	All API endpoints are protected by default
	•	Clients must provide a valid Bearer token
	•	Token-based auth keeps the system stateless and scalable

Authentication Flow
	1.	Obtain an access & refresh token:
        POST /api/token/
    Payload:
        {
            "username": "user",
            "password": "password"
        }

    2.	Use the access token in subsequent requests:
        Authorization: Bearer <access_token>

    3.	Refresh expired access tokens:
        POST /api/token/refresh/


## RBAC Rules

The system distinguishes between regular authenticated users and staff (admin) users.

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

⸻

🧭 RBAC-Protected Endpoints

Geofence Management
    Endpoint                Method              Access
    /api/geofences/         GET                 Authenticated
    /api/geofences/         POST                Staff only
    /api/geofences/{id}/    PUT                 Staff only
    /api/geofences/{id}/    DELETE              Staff only

Drone Safety Override
     Endpoint                       Method              Access
/api/drones/{serial}/mark-safe/     POST                Staff only


Design Note

RBAC is enforced at the view layer using:
	•	IsAuthenticated (baseline access)
	•	IsAdminUser and explicit is_staff checks for privileged actions

This keeps authorization rules:
	•	Explicit
	•	Auditable
	•	Easy to extend later (e.g., roles, scopes, or per-object permissions)











            

