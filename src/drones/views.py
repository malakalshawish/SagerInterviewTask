from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Drone
from .serializers import DroneSerializer

# Create your views here.
class DroneListView(APIView):
    #function that gets called when a GET request is made to this endpoint
    def get(self, request):
        #drones is now a list-like object of drone instances
        drones = Drone.objects.all()
        serializer = DroneSerializer(drones, many=True)
        #DRF turns it into JSON + HTTP 200
        return Response(serializer.data)

