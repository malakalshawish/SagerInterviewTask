from rest_framework import serializers
from .models import DroneTelemetry

#output serialization: how to turn a DroneTelemetry object into JSON when sending a response
#ModelSerializer is a DRF class that automatically generates a serializer based on a Django model
#by defining a Meta class inside the serializer, we specify which model to use and which fields to include in the serialized output
#this means that when we return a DroneTelemetry object in a response, it will be converted to JSON with the specified fields

#How should stored telemetry rows be presented to the outside world?
class DroneTelemetrySerializer(serializers.ModelSerializer):
    # Takes database rows (DroneTelemetry objects)
    # Selects which fields to expose
    # Converts Python objects → JSON
    # Formats timestamps, floats, etc.
    # Does NOT validate input
    
    class Meta:
        model = DroneTelemetry
        fields = [
            "id",
            "timestamp",
            "lat",
            "lng",
            "height_m",
            "horizontal_speed_mps",
        ]
