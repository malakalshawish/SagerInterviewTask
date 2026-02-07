from django.contrib import admin
from .models import Drone, DroneTelemetry

# Register your models here.
admin.site.register(Drone)
admin.site.register(DroneTelemetry)

