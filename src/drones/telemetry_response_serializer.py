from rest_framework import serializers

#response serialization: defines the structure of the JSON response we send back to the client after ingesting telemetry data
#this serializer is used to format the response data that we return after successfully processing incoming telemetry data
#by defining the fields in this serializer, we specify what information about the drone and telemetry 
#record will be included in the response sent back to the client after ingesting telemetry data

#"After we process incoming telemetry data, what information do we want to send back to the client about the drone and the telemetry record that was created?"
class TelemetryIngestResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()
    drone_id = serializers.IntegerField()
    telemetry_id = serializers.IntegerField()