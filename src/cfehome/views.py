from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView
from drones.serializers import DroneSerializer
from drones.telemetry_in_serializer import TelemetryInSerializer
from drones.serializers import DroneTelemetrySerializer

PROJECT_NAME = getattr(settings, "PROJECT_NAME", "Unset Project Views")

def hello_world(request):
    return render(request, "hello-world.html", {"project_name" : PROJECT_NAME})

def health_view(request):
    return HttpResponse("OK")
    
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
    
    
