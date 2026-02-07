from django.db import models
from django.utils import timezone


# Create your models here.
#represents database table
#every model.<field> becomes a column in the database
class Drone(models.Model):
    #nulls are allowed for some values
    #some fields are allowed to be blank
    
    
    #what identifies a drone? serial 
    serial = models.CharField(max_length=64, unique=True, db_index=True)
    
    #latest known state
    last_seen = models.DateTimeField(null=True, blank=True, db_index=True)
    last_lat = models.FloatField(null=True, blank=True)
    last_lng = models.FloatField(null=True, blank=True)
    
    #dangerous classification
    #json for list storage
    is_dangerous = models.BooleanField(default=False, db_index=True)
    danger_reasons = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.serial


class DroneTelemetry(models.Model):
    #who does this belong to? should be exactly one drone per telemetry record
    drone = models.ForeignKey(Drone, on_delete=models.CASCADE, related_name="telemetry")
    
    #when did this telemetry record occur?
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)    
    #where was the drone?
    lat = models.FloatField()
    lng = models.FloatField()
    
    height_m = models.FloatField(null=True, blank=True)
    horizontal_speed_mps = models.FloatField(null=True, blank=True)
    
    #configuration class
    #instructions about the table
    #inside this class to scope configuration to this model
    class Meta:
        indexes = [
            models.Index(fields=["drone", "timestamp"]),
        ]
        ordering = ["timestamp"]
    
