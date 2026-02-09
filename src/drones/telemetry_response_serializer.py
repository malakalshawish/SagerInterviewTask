from rest_framework import serializers

class TelemetryIngestResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()
    drone_id = serializers.IntegerField()
    telemetry_id = serializers.IntegerField()