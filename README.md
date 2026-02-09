Overview

This project is a Django + Django REST Framework backend that ingests drone telemetry, stores historical data in PostgreSQL, and exposes multiple APIs to query drone state, location, danger status, and flight paths.

The system is designed with a clear separation between:
	•	Current drone state (summary)
	•	Historical telemetry (time-series data)
	•	Derived business logic (online status, danger classification, proximity)

Swagger/OpenAPI documentation is included.

⸻

Tech Stack
	•	Python
	•	Django
	•	Django REST Framework
	•	PostgreSQL (Railway)
	•	drf-spectacular (OpenAPI / Swagger)

⸻

Setup Instructions

1. Clone and create virtual environment
    python -m venv venv
    source venv/bin/activate

2. Install dependencies
    pip install -r requirements.txt

3. Environment variables
    Create a .env file with:
        DJANGO_SECRET_KEY=your-secret-key
        DEBUG=True
        DATABASE_URL=postgres://...

4. Run migrations
    python manage.py migrate

5. Create admin user
    python manage.py createsuperuser

6. Run server
    python manage.py runserver

⸻

API Documentation (Swagger)
	•	Swagger UI:
        /api/docs/

    •	OpenAPI schema:
        /api/schema/

⸻

API Endpoints

Drone APIs
	•	GET /api/drones/
List all drones
Optional filter: ?serial=DRONE
	•	GET /api/drones/online/
Drones considered online (last_seen within 30 seconds)
	•	GET /api/drones/nearby/?lat=...&lng=...
Drones within 5 km of the given location
	•	GET /api/drones/dangerous/
List all dangerous drones with reasons


Telemetry APIs
	•	POST /api/telemetry/
Ingest telemetry data

Example payload:
{
  "serial": "DRONE001",
  "lat": 31.9539,
  "lng": 35.9106,
  "height_m": 600,
  "horizontal_speed_mps": 12
}

	•	GET /api/drones/<serial>/telemetry/
Get full telemetry history for a drone
	•	GET /api/drones/<serial>/path/
GeoJSON LineString representing the drone’s flight path
(coordinates are returned as [lng, lat])

⸻

Data Model

Drone

Represents the current state of a drone:
	•	serial (unique)
	•	last_seen
	•	last_lat / last_lng
	•	is_dangerous
	•	danger_reasons

DroneTelemetry

Represents historical telemetry points:
	•	timestamp
	•	lat / lng
	•	height_m
	•	horizontal_speed_mps

⸻

Business Rules

Online Drones

A drone is considered online if:
    last_seen >= now - 30 seconds

Nearby Drones

A drone is considered nearby if:
    distance <= 5 km
Distance is calculated using the Haversine formula.

Dangerous Drones

A drone is marked dangerous if any rule is triggered:
	•	height_m > 500
	•	horizontal_speed_mps > 10

Reasons are stored on the Drone record as a list.

⸻

Tests

Automated tests cover:
	•	telemetry ingestion
	•	danger classification
	•	nearby validation
	•	GeoJSON path output

Run tests with:
    python manage.py test

⸻

MQTT 

The system is designed to support MQTT ingestion via a background worker.
An MQTT consumer can reuse the same telemetry ingestion logic used by the HTTP endpoint.

This separation ensures:
	•	consistent validation
	•	single source of business logic
	•	easy extensibility

⸻

Notes / Assumptions
	•	Online window: 30 seconds
	•	Nearby radius: 5 km
	•	GeoJSON uses [lng, lat] coordinate order
	•	PostgreSQL used for persistence

## Database / Deployment
The application uses PostgreSQL hosted on Railway.
The `DATABASE_URL` environment variable is used for both local development and deployment.

No code changes are required when switching between local and Railway environments.