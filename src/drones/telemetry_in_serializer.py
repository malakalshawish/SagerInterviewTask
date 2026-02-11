from rest_framework import serializers

#input deserialization: defines what fields we expect to receive in incoming telemetry data and how to validate them
#this serializer is used to validate and parse incoming telemetry data before we save it to the database
#by defining the fields and their types, we ensure that the incoming data is in the correct format and contains all required information
#serializers.Serializer is a DRF class that allows us to define custom serializers that are not directly tied to a Django model, 
# #which is useful for validating input data that may not correspond directly to a model instance


#Is this incoming telemetry payload valid, safe, and usable?
class TelemetryInSerializer(serializers.Serializer):
    serial = serializers.CharField(max_length=64)
    lat = serializers.FloatField()
    lng = serializers.FloatField()

    timestamp = serializers.DateTimeField(required=False)

    # Accept both naming styles
    height_m = serializers.FloatField(required=False)
    horizontal_speed_mps = serializers.FloatField(required=False)

    height = serializers.FloatField(required=False, write_only=True)
    speed = serializers.FloatField(required=False, write_only=True)

    def validate(self, attrs):
        # Map legacy keys -> canonical keys if canonical not provided
        if "height_m" not in attrs and "height" in attrs:
            attrs["height_m"] = attrs["height"]

        if "horizontal_speed_mps" not in attrs and "speed" in attrs:
            attrs["horizontal_speed_mps"] = attrs["speed"]

        return attrs
