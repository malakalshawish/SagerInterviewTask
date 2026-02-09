from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter

from .models import Drone, DroneTelemetry
from .serializers import DroneSerializer
from .telemetry_in_serializer import TelemetryInSerializer
from .telemetry_out_serializer import DroneTelemetrySerializer
from .utils import haversine_km
from .telemetry_response_serializer import TelemetryIngestResponseSerializer
from .services import ingest_telemetry

# Alias for backward compatibility
TelemetryOutSerializer = DroneTelemetrySerializer


#decorator that adds schema information for API documentation generation, specifying the expected response format and tags for categorization

# Create your views here.
#each view corresponds to an endpoint in urls.py
class DroneListView(APIView):
    @extend_schema(
    responses=DroneSerializer(many=True),
    tags=["drones"],
    )
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
    @extend_schema(
        responses=DroneSerializer(many=True),
        tags=["drones"],
    )

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
    @extend_schema(
    parameters=[
        OpenApiParameter("lat", float, OpenApiParameter.QUERY, required=True),
        OpenApiParameter("lng", float, OpenApiParameter.QUERY, required=True),
    ],
    responses=DroneSerializer(many=True),
    tags=["drones"],
    )
    
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
    @extend_schema(
        request=TelemetryInSerializer,
        responses={201: TelemetryIngestResponseSerializer},
        tags=["telemetry"],
    )
    def post(self, request):
        serializer = TelemetryInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # We moved all database work + business logic (get_or_create, create telemetry,
        # danger rules, and updating the drone's latest state) into services.py so it can be reused
        # by BOTH the HTTP endpoint and the MQTT consumer.
        #
        # The view now only does:
        # 1) validate input (serializer)
        # 2) delegate to ingest_telemetry()
        # 3) return an HTTP response

        drone, telemetry = ingest_telemetry(data)

        return Response(
            {
                "detail": "Telemetry ingested",
                "drone_id": drone.id,
                "telemetry_id": telemetry.id,
            },
            status=status.HTTP_201_CREATED,
        )
            



class DroneTelemetryListView(APIView):
    #404 if serial doesn’t exist
    #returns telemetry points ordered by timestamp for a given drone serial number
    @extend_schema(
    responses=DroneTelemetrySerializer(many=True),
    tags=["telemetry"],
    )
    def get(self, request, serial):
        drone = get_object_or_404(Drone, serial=serial)
        #query the database for telemetry records associated with the drone, ordered by timestamp
        qs = DroneTelemetry.objects.filter(drone=drone).order_by("timestamp")
        #serialize the queryset of telemetry records into a list of dictionaries and return as JSON
        serializer = DroneTelemetrySerializer(qs, many=True)
        return Response(serializer.data)
    


    #the GeoJSON format is a standard for representing geographic data structures, 
    # and in this case, we are creating a LineString geometry that represents the path of the drone 
    # based on its recorded latitude and longitude coordinates over time.
class DronePathGeoJSONView(APIView):
    #404 if serial doesn’t exist
    #returns a GeoJSON representation of the drone's path based on its telemetry data, which
    #can be used for mapping applications or spatial analysis
    @extend_schema(
    responses={
        200: OpenApiResponse(
            response=dict,
            description="GeoJSON flight path"
        )
    },
    tags=["drones"],
    )
    def get(self, request, serial):
        drone = get_object_or_404(Drone, serial=serial)
        #query the database for telemetry records associated with the drone, ordered by timestamp
        qs = DroneTelemetry.objects.filter(drone=drone).order_by("timestamp").values_list("lng", "lat")
        #values_list with "lng" and "lat" will return a list of tuples like [(lng1, lat1), (lng2, lat2), ...]
        #we convert this queryset into a list of [lng, lat] pairs to fit the GeoJSON format, 
        # which expects coordinates in the form of [longitude, latitude]
        coordinates = list(qs)

        return Response(
            {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": coordinates},
                "properties": {"serial": drone.serial, "count": len(coordinates)},
            }
        )

# this view returns a list of drones that are classified as dangerous, 
# which can be used by clients to identify potential threats or hazards in the area 
# based on the latest telemetry data and the defined criteria for dangerous behavior. 
# By filtering the drones based on their dangerous classification, 
# this endpoint allows clients to quickly access information about drones that may pose a risk, 
# enabling them to take appropriate actions or precautions.
class DangerousDroneListView(APIView):
    @extend_schema(
    responses=DroneSerializer(many=True),
    tags=["drones"],
    )

    def get(self, request):
        #query the database for drones that are classified as dangerous, ordered by serial number
        qs = Drone.objects.filter(is_dangerous=True).order_by("serial")
        serializer = DroneSerializer(qs, many=True)
        return Response(serializer.data)