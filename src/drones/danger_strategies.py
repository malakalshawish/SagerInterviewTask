from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Optional
from django.conf import settings
from drones.utils import haversine_km


class DangerRule(Protocol):
    def check(
        self,
        *,
        height_m: Optional[float],
        horizontal_speed_mps: Optional[float],
    ) -> Optional[str]:
        """Return a reason string if dangerous, else None."""
        ...


@dataclass(frozen=True)
class HeightRule:
    threshold_m: float = 500.0

    def check(self, *, height_m: Optional[float], horizontal_speed_mps: Optional[float]) -> Optional[str]:
        if height_m is not None and height_m > self.threshold_m:
            return f"Altitude greater than {int(self.threshold_m)} meters"
        return None


@dataclass(frozen=True)
class SpeedRule:
    threshold_mps: float = 10.0

    def check(self, *, height_m: Optional[float], horizontal_speed_mps: Optional[float]) -> Optional[str]:
        if horizontal_speed_mps is not None and horizontal_speed_mps > self.threshold_mps:
            return f"Horizontal speed greater than {int(self.threshold_mps)} m/s"
        return None


class DangerClassifier:
    """Strategy context that applies a set of rules."""
    def __init__(self, rules: list[DangerRule]):
        self.rules = rules

    def classify(
        self,
        *,
        height_m: Optional[float],
        horizontal_speed_mps: Optional[float],
    ) -> list[str]:
        reasons: list[str] = []
        for rule in self.rules:
            reason = rule.check(height_m=height_m, horizontal_speed_mps=horizontal_speed_mps)
            if reason:
                reasons.append(reason)
        return reasons


class CombinedClassifier:
    def __init__(self):
        self.thresholds = DangerClassifier([HeightRule(), SpeedRule()])
        self.geofence = GeofenceClassifier()

    def classify(self, *, height_m=None, horizontal_speed_mps=None, lat=None, lng=None) -> list[str]:
        reasons = self.thresholds.classify(
            height_m=height_m,
            horizontal_speed_mps=horizontal_speed_mps,
        )
        reasons += self.geofence.classify(lat=lat, lng=lng)
        return reasons


def default_classifier():
    return CombinedClassifier()


#data class is a Python decorator that automatically generates special methods like __init__ and __repr__ for classes that are primarily used to store data, 
# making it easier to create classes that are simple containers for data without having to write boilerplate code for initialization and representation.
@dataclass
class GeofenceClassifier:
    def classify(self, *, lat: float | None, lng: float | None) -> list[str]:
        #this method checks if the given latitude and longitude coordinates of a drone are within any predefined no-fly zones,
        reasons: list[str] = []
        #if either the latitude or longitude is None, we cannot perform the geofence classification, so we return an empty list of reasons, 
        #indicating that we cannot determine if the drone is in a no-fly zone or not based on the provided coordinates
        if lat is None or lng is None:
            return reasons
        #we retrieve the list of no-fly zones from the Django settings, which is expected to be a list of dictionaries containing the latitude, longitude, radius in kilometers, and name of each no-fly zone.
        zones = getattr(
            settings,
            "DRONE_GEOFENCE_ZONES",
            getattr(settings, "NO_FLY_ZONES", []),
        )
        for zone in zones:
            distance = haversine_km(lat, lng, zone["lat"], zone["lng"])
            #we calculate the distance between the drone's coordinates and the center of each no-fly zone using the haversine_km function, 
            #which computes the great-circle distance between two points on the Earth's surface based on their latitude and longitude.
            if distance <= zone["radius_km"]:
                reasons.append(f'Entered no-fly zone: {zone["name"]}')

        return reasons
