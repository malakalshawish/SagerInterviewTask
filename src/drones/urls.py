from django.urls import path
from .views import DroneListView, NearbyDroneListView, OnlineDroneListView


urlpatterns = [
    # endpoints will go here next
    path("drones/", DroneListView.as_view(), name="drone-list"),
    path("drones/online/", OnlineDroneListView.as_view(), name="online-drone-list"),
    path("drones/nearby/", NearbyDroneListView.as_view(), name="nearby-drone-list"),
]
