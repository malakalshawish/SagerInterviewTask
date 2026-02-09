from rest_framework import serializers

#input deserialization: defines what fields we expect to receive in incoming telemetry data and how to validate them
#this serializer is used to validate and parse incoming telemetry data before we save it to the database
#by defining the fields and their types, we ensure that the incoming data is in the correct format and contains all required information
#serializers.Serializer is a DRF class that allows us to define custom serializers that are not directly tied to a Django model, 
# #which is useful for validating input data that may not correspond directly to a model instance


#Is this incoming telemetry payload valid, safe, and usable?
class TelemetryInSerializer(serializers.Serializer):
    # Validates raw JSON sent by a client / MQTT
    # Ensures required fields exist
    # Ensures types are correct
    # Converts strings → Python types
    # Does NOT talk to the database
    
    #required fields for incoming telemetry data
    serial = serializers.CharField(max_length=64)
    lat = serializers.FloatField()
    lng = serializers.FloatField()
    
    #optional fields for incoming telemetry data
    timestamp = serializers.DateTimeField(required=False)
    height_m = serializers.FloatField(required=False)
    horizontal_speed_mps = serializers.FloatField(required=False)
