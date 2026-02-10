from django.utils import timezone
from .models import Drone, DroneTelemetry
from .danger_strategies import default_classifier

#what this does: takes validated telemetry data (already validated by TelemetryInSerializer), writes DroneTelemetry, 
#updates Drone latest state + danger classification, and returns (drone, telemetry).

def ingest_telemetry(validated_data: dict) -> tuple[Drone, DroneTelemetry]:
    """
    Takes validated telemetry data (already validated by TelemetryInSerializer),
    writes DroneTelemetry, updates Drone latest state + danger classification,
    and returns (drone, telemetry).
    """
    #the serial number is the unique identifier for the drone, so we extract it from the validated data to find or create the corresponding Drone record in the database
    serial = validated_data["serial"]

    #get_or_create is a Django method that tries to find an existing record with the given parameters, 
    #and if it doesn't find one, it creates a new record with those parameters. 
    #It returns a tuple of (object, created), where object is the retrieved or created instance, 
    #and created is a boolean indicating whether a new record was created (True) or an existing record was found (False).
    drone, _ = Drone.objects.get_or_create(serial=serial)

    # If no timestamp is provided in the telemetry data, use the current time as the timestamp for the telemetry record. 
    #This ensures that every telemetry record has a valid timestamp, even if the client doesn't provide one.
    timestamp = validated_data.get("timestamp") or timezone.now()

    #create a new DroneTelemetry record in the database with the provided telemetry data, associating it with the corresponding Drone record.
    #the height_m and horizontal_speed_mps fields are optional, so we use the get method on the validated_data dictionary to retrieve their values, 
    #which will return None if they are not provided in the input data
    telemetry = DroneTelemetry.objects.create(
        drone=drone,
        timestamp=timestamp,
        lat=validated_data["lat"],
        lng=validated_data["lng"],
        height_m=validated_data.get("height_m"),
        horizontal_speed_mps=validated_data.get("horizontal_speed_mps"),
    )

    #danger classification logic: we check the height and horizontal speed values from the telemetry data 
    #against predefined thresholds (500 meters for height and 10 m/s for speed).
    #If the height exceeds 500 meters, we add a reason to the reasons list indicating that the altitude is too high. 
    #If the horizontal speed exceeds 10 m/s, we add another reason indicating that the speed is too high. 
    #Finally, we set the is_dangerous flag on the Drone record to True if there are any reasons in the list, 
    #and we save the updated Drone record to the database with the new latest state and danger classification information.
    classifier = default_classifier()
    reasons = classifier.classify(
    height_m=validated_data.get("height_m"),
    horizontal_speed_mps=validated_data.get("horizontal_speed_mps"),
    lat=validated_data["lat"],
    lng=validated_data["lng"],
    )

    drone.is_dangerous = len(reasons) > 0
    drone.danger_reasons = reasons

    #latest state: we update the Drone's last seen timestamp and location based on the incoming telemetry data.
    #the last_seen field is updated to the timestamp of the telemetry record, which represents the most recent time we received telemetry data from this drone. 
    #the last_lat and last_lng fields are updated to the latitude and longitude values from the telemetry data, representing the drone's latest known location.
    # latest state
    drone.last_seen = timestamp
    drone.last_lat = validated_data["lat"]
    drone.last_lng = validated_data["lng"]

    drone.save(
        update_fields=[
            "last_seen",
            "last_lat",
            "last_lng",
            "is_dangerous",
            "danger_reasons",
        ]
    )

    return drone, telemetry