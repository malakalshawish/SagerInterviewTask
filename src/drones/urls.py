from django.urls import path
from .views import DroneListView


urlpatterns = [
    # endpoints will go here next
    path("drones/", DroneListView.as_view(), name="drone-list"),
]
