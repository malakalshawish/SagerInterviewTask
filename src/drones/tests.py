# Create your tests here.

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status

from drones.models import Drone, DroneTelemetry


class DroneAPITests(APITestCase):
    #setUp is a special method that gets called before each test method runs, allowing us to set up any necessary data or state for the tests
    #in this case, we just define a serial number that we can use in our tests to create and query drones
    #this means that before each test method is executed, self.serial will be set to "DRONE001"
    #this allows us to avoid repeating the same setup code in each test method and ensures that each test starts with a consistent state
    #if we needed to create a drone instance in the database for our tests, we could also do that in the setUp method so that it is available for all test methods
    def setUp(self):
        self.serial = "DRONE001"

    #test method names should start with "test_" so that the test runner recognizes them as tests to execute
    #this test checks that when we post telemetry data to the telemetry ingest endpoint, it creates
    #a new DroneTelemetry record in the database and updates the corresponding Drone's last seen timestamp and location
    def test_telemetry_post_creates_row_and_updates_drone(self):
        url = reverse("telemetry-ingest")
        payload = {"serial": self.serial, "lat": 31.9539, "lng": 35.9106}
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        drone = Drone.objects.get(serial=self.serial)
        self.assertIsNotNone(drone.last_seen)
        self.assertEqual(drone.last_lat, payload["lat"])
        self.assertEqual(drone.last_lng, payload["lng"])

        self.assertEqual(DroneTelemetry.objects.filter(drone=drone).count(), 1)

    #this test checks that when we post telemetry data with a height greater than 500 meters or a horizontal speed greater than 10 m/s, 
    #the corresponding Drone is marked as dangerous and the appropriate danger reasons are added to the drone's record
    def test_danger_flags_set_when_height_or_speed_exceeds_threshold(self):
        url = reverse("telemetry-ingest")
        payload = {
            "serial": self.serial,
            "lat": 31.9539,
            "lng": 35.9106,
            "height_m": 600,
            "horizontal_speed_mps": 12,
        }
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        drone = Drone.objects.get(serial=self.serial)
        self.assertTrue(drone.is_dangerous)
        self.assertIn("Altitude greater than 500 meters", drone.danger_reasons)
        self.assertIn("Horizontal speed greater than 10 m/s", drone.danger_reasons)

    #this test checks that when we try to access the nearby drones endpoint without providing the required latitude and longitude parameters, 
    #we get a 400 Bad Request response, indicating that the request was invalid due to missing required parameters
    def test_nearby_requires_lat_lng(self):
        url = reverse("nearby-drone-list")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    #this test checks that when we access the drone path endpoint for a given drone serial number, 
    #we get a GeoJSON response that contains a LineString geometry with coordinates in the correct order (longitude, latitude)
    #the test creates a drone and two telemetry points, then makes a GET request to the drone path endpoint and verifies that 
    #the response is a valid GeoJSON Feature with a LineString geometry, and that the coordinates are in the correct order (longitude first, then latitude)
    def test_path_returns_geojson_and_lng_lat_order(self):
        # create drone + two telemetry points
        drone = Drone.objects.create(serial=self.serial, last_seen=timezone.now(), last_lat=31.0, last_lng=35.0)
        #create two telemetry records for the drone with different timestamps and locations
        DroneTelemetry.objects.create(
            drone=drone, timestamp=timezone.now(), lat=31.0, lng=35.0, height_m=100, horizontal_speed_mps=5
        )
        DroneTelemetry.objects.create(
            drone=drone, timestamp=timezone.now(), lat=31.1, lng=35.1, height_m=100, horizontal_speed_mps=5
        )
        #make a GET request to the drone path endpoint for the created drone and verify that the response 
        #is a valid GeoJSON Feature with a LineString geometry, and that the coordinates are in the correct order (longitude first, then latitude)
        url = reverse("drone-path-geojson", kwargs={"serial": self.serial})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        #the response should be a GeoJSON Feature with a LineString geometry, and the coordinates should be in [longitude, latitude] order
        body = res.json()
        self.assertEqual(body["type"], "Feature")
        self.assertEqual(body["geometry"]["type"], "LineString")

        coords = body["geometry"]["coordinates"]
        self.assertTrue(len(coords) >= 2)

        # coords should be [lng, lat]
        first = coords[0]
        self.assertEqual(first[0], 35.0)  # lng
        self.assertEqual(first[1], 31.0)  # lat