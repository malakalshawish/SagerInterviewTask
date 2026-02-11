from django.urls import path
from .views import (
    DroneListView,
    MarkDroneSafeView,
    OnlineDroneListView,
    NearbyDroneListView,
    TelemetryIngestView,
    DroneTelemetryListView,
    DronePathGeoJSONView,
    DangerousDroneListView,
    GeofenceZoneListCreateView,
    GeofenceZoneDetailView,
)

urlpatterns = [
    # endpoints will go here next
    path("drones/", DroneListView.as_view(), name="drone-list"),
    path("drones/online/", OnlineDroneListView.as_view(), name="online-drone-list"),
    path("drones/nearby/", NearbyDroneListView.as_view(), name="nearby-drone-list"),
    path("telemetry/", TelemetryIngestView.as_view(), name="telemetry-ingest"),
    path("drones/<str:serial>/telemetry/", DroneTelemetryListView.as_view(), name="drone-telemetry"),
    path("drones/<str:serial>/path/", DronePathGeoJSONView.as_view(), name="drone-path-geojson"),
    path("drones/dangerous/", DangerousDroneListView.as_view(), name="dangerous-drone-list"),
    path("drones/<str:serial>/mark-safe/", MarkDroneSafeView.as_view(), name="drone-mark-safe"),
    path("geofences/", GeofenceZoneListCreateView.as_view(), name="geofence-zone-list-create"),
    path("geofences/<int:pk>/", GeofenceZoneDetailView.as_view(), name="geofence-zone-detail"),
]
