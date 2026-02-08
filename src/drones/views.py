from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Drone
from .serializers import DroneSerializer
from django.utils import timezone
from datetime import timedelta


# Create your views here.
#each view corresponds to an endpoint in urls.py
class DroneListView(APIView):
    #function that gets called when a GET request is made to this endpoint
    def get(self, request):
        """
        Retrieve a list of drones, optionally filtered by serial number.

        This method handles GET requests to fetch drone records from the database.
        It supports optional filtering by serial number using a case-insensitive
        partial match.

        Args:
            request: The HTTP request object containing query parameters.

        Query Parameters:
            serial (str, optional): Filter drones by serial number (case-insensitive,
                partial match). Example: ?serial=abc123

        Returns:
            Response: A DRF Response object containing:
                - Serialized list of drone objects matching the criteria
                - HTTP 200 status code

        Example:
            GET /api/drones/              # Returns all drones
            GET /api/drones/?serial=abc   # Returns drones with 'abc' in serial number
        """
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




