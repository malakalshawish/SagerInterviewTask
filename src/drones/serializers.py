#translates between Python objects and JSON.
#defines how a Drone object is turned into JSON when your API sends a response.
from rest_framework import serializers
from .models import Drone


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
