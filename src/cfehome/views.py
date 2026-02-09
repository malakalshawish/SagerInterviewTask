from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView
from .serializers import DroneSerializer, TelemetryInSerializer, DroneTelemetrySerializer

    
@extend_schema(responses=DroneSerializer(many=True), tags=["drones"])
class DroneListView(APIView):
    ...
    
@extend_schema(responses=DroneSerializer(many=True), tags=["drones"])
class OnlineDroneListView(APIView):
    ...
    
@extend_schema(request=TelemetryInSerializer,responses={201: dict},tags=["telemetry"])
class TelemetryIngestView(APIView):
    ...

@extend_schema(responses=DroneTelemetrySerializer(many=True), tags=["telemetry"])
class DroneTelemetryListView(APIView):
    ...
    
@extend_schema(responses=dict, tags=["drones"])
class DronePathGeoJSONView(APIView):
    ... 
    
@extend_schema(responses=DroneSerializer(many=True), tags=["drones"])
class DangerousDroneListView(APIView):
    ...
    
    
