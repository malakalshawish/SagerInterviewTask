from ast import If
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Drone
from .serializers import DroneSerializer
from django.utils import timezone
from datetime import timedelta
from .utils import haversine_km
from rest_framework import status
from .telemetry_serializer import TelemetryInSerializer
from .models import Drone, DroneTelemetry




# Create your views here.
#each view corresponds to an endpoint in urls.py
class DroneListView(APIView):
    #function that gets called when a GET request is made to this endpoint
    def get(self, request):
        # Retrieve a list of drones, optionally filtered by serial number.

        # This method handles GET requests to fetch drone records from the database.
        # It supports optional filtering by serial number using a case-insensitive
        # partial match.

        # Args:
        #     request: The HTTP request object containing query parameters.

        # Query Parameters:
        #     serial (str, optional): Filter drones by serial number (case-insensitive,
        #         partial match). Example: ?serial=abc123

        # Returns:
        #     Response: A DRF Response object containing:
        #         - Serialized list of drone objects matching the criteria
        #         - HTTP 200 status code

        # Example:
        #     GET /api/drones/              # Returns all drones
        #     GET /api/drones/?serial=abc   # Returns drones with 'abc' in serial number
        
        #drones is now a list-like object of drone instances
        serial = request.query_params.get("serial")
        #serial filtering example: /api/drones/?serial=abc123 would return drones with "abc123" in their serial number
        if serial:
            drones = Drone.objects.filter(serial__icontains=serial)
        else:
            drones = Drone.objects.all()
        serializer = DroneSerializer(drones, many=True)
        #DRF turns it into JSON + HTTP 200
        return Response(serializer.data)


class OnlineDroneListView(APIView):
    # Retrieve a list of drones that are currently online.
    # This method handles GET requests to fetch drone records that are considered "online" based on their last seen timestamp. 
    # A drone is considered online if it has been seen within the last 30 seconds.
    # Returns:
    #     Response: A DRF Response object containing:
    #         - Serialized list of online drone objects
    #         - HTTP 200 status code
    # Example:
    # GET /api/drones/online/  # Returns drones seen in the last 30 seconds


    def get(self, request):
        #define "online" as seen in the last 30 seconds
        #cutoff means the latest time a drone could have been seen to be considered online
        cutoff = timezone.now() - timedelta(seconds=30)
        #asks the DB for drones whose last_seen is greater than or equal to the cutoff
        drones = Drone.objects.filter(last_seen__gte=cutoff)
        #convert the queryset of drone instances into a list of dictionaries using the serializer
        #to JSON object
        serializer = DroneSerializer(drones, many=True)
        return Response(serializer.data)


class NearbyDroneListView(APIView):
    # read query params
    # validate presence
    # validate numeric
    # fetch drones with coordinates
    # compute distance
    # filter within 5 km
    # return JSON

    def get(self, request):
        #query parameters are strings
        lat = request.query_params.get("lat")
        lng = request.query_params.get("lng")
        #validate that lat and lng are present and can be converted to floats
        if lat is None or lng is None:
            return Response({"detail": "Query parameters 'lat' and 'lng' are required."},
            status=status.HTTP_400_BAD_REQUEST,)
        try:
            lat = float(lat)
            lng = float(lng)
        except (TypeError, ValueError):
            return Response({"detail": "Query parameters 'lat' and 'lng' must be valid numbers."},
            status=status.HTTP_400_BAD_REQUEST,)
        #fetch drones with known coordinates
        drones = Drone.objects.exclude(last_lat__isnull=True).exclude(last_lng__isnull=True)
        
        #calculate distance from each drone to the provided lat/lng and filter to those within 5 km
        nearby = []
        for drone in drones:
            distance = haversine_km(lat, lng, drone.last_lat, drone.last_lng)
            if distance <= 5:
                nearby.append(drone)
        #serialize the nearby drones and return as JSON
        serializer = DroneSerializer(nearby, many=True)
        return Response(serializer.data)
            

#handle POST requests to ingest telemetry data from drones
#send data to a server to create a new resource or trigger an action
class TelemetryIngestView(APIView):
    # Wraps the incoming JSON in serializer
    # Validates required fields and types
    # If invalid → DRF automatically returns a clean 400 with details
    # If valid → you get data as clean Python values (floats, datetime)

    def post(self, request):
        serializer = TelemetryInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        serial = data["serial"]
        #get_or_create is a Django method that tries to find an existing record with the given parameters, 
        # and if it doesn't find one, it creates a new record with those parameters. 
        #It returns a tuple of (object, created), where object is the retrieved or created instance, 
        #and created is a boolean indicating whether a new record was created.
        drone, _ = Drone.objects.get_or_create(
            serial=serial,
        )
        timestamp = data.get("timestamp") or timezone.now()
        #update the drone's last seen info with the latest telemetry data
        telemetry = DroneTelemetry.objects.create(
            drone=drone,
            timestamp=timestamp,
            lat=data["lat"],
            lng=data["lng"],
            height_m=data.get("height_m"),
            horizontal_speed_mps=data.get("horizontal_speed_mps"),
        )
        reasons = []

        height_m = data.get("height_m")
        speed_mps = data.get("horizontal_speed_mps")

        if height_m is not None and height_m > 500:
            reasons.append("Altitude greater than 500 meters")

        if speed_mps is not None and speed_mps > 10:
            reasons.append("Horizontal speed greater than 10 m/s")

        drone.is_dangerous = len(reasons) > 0
        drone.danger_reasons = reasons

        #update the drone's latest known state with the telemetry data
        drone.last_seen = timestamp
        drone.last_lat = data["lat"]
        drone.last_lng = data["lng"]
        drone.save(update_fields=["last_seen", "last_lat", "last_lng", "is_dangerous", "danger_reasons"])
        return Response({"detail": "Telemetry ingested", "drone_id": drone.id, "telemetry_id": telemetry.id},
        status=status.HTTP_201_CREATED,)






