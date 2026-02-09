#translates between Python objects and JSON.
#defines how a Drone object is turned into JSON when your API sends a response.
from rest_framework import serializers
from .models import Drone

#output serialization: how to turn a Drone object into JSON when sending a response
#ModelSerializer is a DRF class that automatically generates a serializer based on a Django model
#by defining a Meta class inside the serializer, we specify which model to use and which fields to include in the serialized output
#this means that when we return a Drone object in a response, it will be converted to JSON with the specified fields
class DroneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Drone
        fields = [
            "id",
            "serial",
            "last_seen",
            "last_lat",
            "last_lng",
            "is_dangerous",
            "danger_reasons",
        ]

