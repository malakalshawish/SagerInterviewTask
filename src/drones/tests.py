# Create your tests here.

from datetime import timedelta
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status

from drones.danger_strategies import default_classifier
from drones.models import Drone, DroneTelemetry
from drones.utils import haversine_km


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
        
        

class DroneAPIEdgeCaseTests(APITestCase):
    def setUp(self):
        self.serial = "EDGE001"
        self.telemetry_url = reverse("telemetry-ingest")

# Telemetry ingest edge cases
    def test_telemetry_missing_serial_returns_400(self):
        #the serial field is required for telemetry ingestion, so if we try to post telemetry data without a serial number,
        #we should get a 400 Bad Request response indicating that the request was invalid due to missing required fields
        payload = {"lat": 31.9539, "lng": 35.9106}
        res = self.client.post(self.telemetry_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        body = res.json()
        self.assertIn("serial", body)

    def test_telemetry_missing_lat_returns_400(self):
        #the lat field is required for telemetry ingestion, so if we try to post telemetry data without a latitude value,
        #we should get a 400 Bad Request response indicating that the request was invalid due to missing required fields
        payload = {"serial": self.serial, "lng": 35.9106}
        res = self.client.post(self.telemetry_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        body = res.json()
        self.assertIn("lat", body)

    def test_telemetry_missing_lng_returns_400(self):
        #the lng field is required for telemetry ingestion, so if we try to post telemetry data without a longitude value,
        #we should get a 400 Bad Request response indicating that the request was invalid due to missing required fields
        payload = {"serial": self.serial, "lat": 31.9539}
        res = self.client.post(self.telemetry_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        body = res.json()
        self.assertIn("lng", body)

    def test_telemetry_invalid_lat_type_returns_400(self):
        #the lat field is expected to be a float, so if we try to post telemetry data with an invalid latitude value (e.g., a string),
        #we should get a 400 Bad Request response indicating that the request was invalid due to incorrect field types
        payload = {"serial": self.serial, "lat": "abc", "lng": 35.9106}
        res = self.client.post(self.telemetry_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        body = res.json()
        self.assertIn("lat", body)

    def test_telemetry_invalid_timestamp_returns_400(self):
        #the timestamp field is expected to be a valid datetime string, so if we try to post telemetry data with an invalid timestamp value (e.g., "not-a-timestamp"),
        #we should get a 400 Bad Request response indicating that the request was invalid due to incorrect field types
        payload = {
            "serial": self.serial,
            "lat": 31.9539,
            "lng": 35.9106,
            "timestamp": "not-a-timestamp",
        }
        res = self.client.post(self.telemetry_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        body = res.json()
        self.assertIn("timestamp", body)

    def test_telemetry_optional_fields_missing_still_201(self):
        #the height_m and horizontal_speed_mps fields are optional for telemetry ingestion, so if we post telemetry data without these fields,
        #we should still get a 201 Created response indicating that the telemetry data was successfully ingested, 
        #and the corresponding DroneTelemetry record should be created in the database with null values for the optional fields
        payload = {"serial": self.serial, "lat": 31.9539, "lng": 35.9106}
        res = self.client.post(self.telemetry_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        drone = Drone.objects.get(serial=self.serial)
        self.assertIsNotNone(drone.last_seen)
        self.assertFalse(drone.is_dangerous)

    def test_danger_boundary_exact_threshold_not_dangerous(self):
        #this test checks that when we post telemetry data with a height exactly equal to 500 meters and a horizontal speed exactly equal to 10 m/s,
        #the corresponding Drone is not marked as dangerous and no danger reasons are added to the drone's record, 
        #since the danger classification logic should only mark a drone as dangerous if the height exceeds 500 meters or the horizontal speed exceeds 10 m/s, 
        #not if they are exactly at the threshold values
        payload = {
            "serial": self.serial,
            "lat": 31.9539,
            "lng": 35.9106,
            "height_m": 500,
            "horizontal_speed_mps": 10,
        }
        res = self.client.post(self.telemetry_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        drone = Drone.objects.get(serial=self.serial)
        self.assertFalse(drone.is_dangerous)
        self.assertEqual(drone.danger_reasons, [])

    def test_danger_just_above_threshold_is_dangerous(self):
        #this test checks that when we post telemetry data with a height just above 500 meters (e.g., 500.0001) and a horizontal speed just above 10 m/s (e.g., 10.0001),
        #the corresponding Drone is marked as dangerous and the appropriate danger reasons are added to the drone's record
        payload = {
            "serial": self.serial,
            "lat": 31.9539,
            "lng": 35.9106,
            "height_m": 500.0001,
            "horizontal_speed_mps": 10.0001,
        }
        res = self.client.post(self.telemetry_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        drone = Drone.objects.get(serial=self.serial)
        self.assertTrue(drone.is_dangerous)
        self.assertTrue(len(drone.danger_reasons) >= 1)

    def test_danger_only_height_sets_only_height_reason(self):
        #this test checks that when we post telemetry data with a height greater than 500 meters but a horizontal speed below 10 m/s,
        #the corresponding Drone is marked as dangerous and the appropriate danger reason for altitude is added to the drone's record
        payload = {
            "serial": self.serial,
            "lat": 31.9539,
            "lng": 35.9106,
            "height_m": 600,
            "horizontal_speed_mps": 5,
        }
        res = self.client.post(self.telemetry_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        drone = Drone.objects.get(serial=self.serial)
        self.assertTrue(drone.is_dangerous)
        self.assertEqual(len(drone.danger_reasons), 1)
        self.assertIn("Altitude", drone.danger_reasons[0])

    def test_danger_only_speed_sets_only_speed_reason(self):
        #this test checks that when we post telemetry data with a horizontal speed greater than 10 m/s but a height below 500 meters,
        #the corresponding Drone is marked as dangerous and the appropriate danger reason for speed is added to the drone's record
        payload = {
            "serial": self.serial,
            "lat": 31.9539,
            "lng": 35.9106,
            "height_m": 100,
            "horizontal_speed_mps": 12,
        }
        res = self.client.post(self.telemetry_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        drone = Drone.objects.get(serial=self.serial)
        self.assertTrue(drone.is_dangerous)
        self.assertEqual(len(drone.danger_reasons), 1)
        self.assertIn("speed", drone.danger_reasons[0].lower())

# Online drones edge cases
    def test_online_includes_seen_within_30_seconds(self):
        #this test checks that when we create a Drone record with a last_seen timestamp within the last 30 seconds,
        #the drone is considered online and is included in the response from the online drones endpoint, 
        # while if we create a Drone record with a last_seen timestamp older than 30 seconds or with a null last_seen value,
        # the drone is considered offline and is not included in the response from the online drones endpoint
        Drone.objects.create(
            serial="ON1",
            last_seen=timezone.now() - timedelta(seconds=29),
            last_lat=31.0,
            last_lng=35.0,
        )
        url = reverse("online-drone-list")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        serials = [d["serial"] for d in res.json()]
        self.assertIn("ON1", serials)

    def test_online_excludes_seen_31_seconds_ago(self):
        #this test checks that when we create a Drone record with a last_seen timestamp older than 30 seconds, 
        #the drone is considered offline and is not included in the response from the online drones endpoint
        Drone.objects.create(
            serial="ON2",
            last_seen=timezone.now() - timedelta(seconds=31),
            last_lat=31.0,
            last_lng=35.0,
        )
        url = reverse("online-drone-list")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        serials = [d["serial"] for d in res.json()]
        self.assertNotIn("ON2", serials)

    def test_online_excludes_last_seen_null(self):
        #this test checks that when we create a Drone record with a null last_seen value,
        #the drone is considered offline and is not included in the response from the online drones endpoint
        Drone.objects.create(serial="ON3", last_seen=None, last_lat=31.0, last_lng=35.0)
        url = reverse("online-drone-list")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        serials = [d["serial"] for d in res.json()]
        self.assertNotIn("ON3", serials)

# Nearby drones edge cases
    def test_nearby_invalid_lat_returns_400(self):
        #this test checks that when we try to access the nearby drones endpoint with an invalid latitude value (e.g., a non-numeric string),
        #we get a 400 Bad Request response indicating that the request was invalid due to incorrect field types for the latitude and longitude parameters
        url = reverse("nearby-drone-list")
        res = self.client.get(url + "?lat=abc&lng=35.0")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nearby_invalid_lng_returns_400(self):
        #this test checks that when we try to access the nearby drones endpoint with an invalid longitude value (e.g., a non-numeric string),
        #we get a 400 Bad Request response indicating that the request was invalid due to incorrect field types for the latitude and longitude parameters
        url = reverse("nearby-drone-list")
        res = self.client.get(url + "?lat=31.0&lng=xyz")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nearby_excludes_drones_with_null_coords(self):
        #this test checks that when we create a Drone record with null latitude and longitude values,
        #the drone is considered offline and is not included in the response from the nearby drones endpoint,
        #since the nearby drones endpoint relies on the last_lat and last_lng fields to determine which drones are nearby, 
        #and if those fields are null, the drone cannot be considered nearby to any location
        Drone.objects.create(serial="NC1", last_seen=timezone.now(), last_lat=None, last_lng=None)
        url = reverse("nearby-drone-list")
        res = self.client.get(url + "?lat=31.0&lng=35.0")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        serials = [d["serial"] for d in res.json()]
        self.assertNotIn("NC1", serials)

    def test_nearby_includes_within_5km_and_excludes_beyond_5km(self):
        #this test checks that when we create Drone records with last_lat and last_lng values that are within 5 kilometers of a given reference point,
        #those drones are included in the response from the nearby drones endpoint, while if we create Drone records with last_lat and 
        #last_lng values that are beyond 5 kilometers of the reference point, 
        #those drones are not included in the response from the nearby drones endpoint, 
        #since the nearby drones endpoint uses the haversine formula to calculate the distance between the drone's last known location 
        #and the provided latitude and longitude parameters, and only includes drones that are within a 5 kilometer radius of the provided location in the response
        # reference point
        q_lat, q_lng = 31.0, 35.0

        # ~4.9 km north (roughly 0.044 degrees latitude ~ 4.9km)
        near_lat = q_lat + 0.044
        far_lat = q_lat + 0.060  # ~6.6km

        Drone.objects.create(serial="NEAR1", last_seen=timezone.now(), last_lat=near_lat, last_lng=q_lng)
        Drone.objects.create(serial="FAR1", last_seen=timezone.now(), last_lat=far_lat, last_lng=q_lng)

        url = reverse("nearby-drone-list")
        res = self.client.get(url + f"?lat={q_lat}&lng={q_lng}")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        serials = [d["serial"] for d in res.json()]

        self.assertIn("NEAR1", serials)
        self.assertNotIn("FAR1", serials)


# Telemetry list + path edge cases
    def test_telemetry_list_unknown_serial_returns_404(self):
        #this test checks that when we try to access the telemetry list endpoint for a drone serial number that does not exist in the database,
        #we get a 404 Not Found response indicating that there is no drone with the specified serial number, and therefore no telemetry data to return for that drone
        url = reverse("drone-telemetry", kwargs={"serial": "DOES_NOT_EXIST"})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_telemetry_list_is_ordered_by_timestamp(self):
        #this test checks that the telemetry list endpoint returns telemetry data ordered by timestamp in ascending order
        drone = Drone.objects.create(serial="ORD1")
        t1 = timezone.now() - timedelta(seconds=10)
        t2 = timezone.now()

        DroneTelemetry.objects.create(drone=drone, timestamp=t2, lat=31.0, lng=35.0)
        DroneTelemetry.objects.create(drone=drone, timestamp=t1, lat=31.1, lng=35.1)

        url = reverse("drone-telemetry", kwargs={"serial": "ORD1"})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        body = res.json()
        # first item should be the earlier timestamp
        self.assertTrue(len(body) >= 2)
        self.assertLessEqual(body[0]["timestamp"], body[1]["timestamp"])

    def test_path_unknown_serial_returns_404(self):
        #this test checks that when we try to access the path endpoint for a drone serial number that does not exist in the database,
        #we get a 404 Not Found response indicating that there is no drone with the specified serial number, and therefore no path data to return for that drone
        url = reverse("drone-path-geojson", kwargs={"serial": "DOES_NOT_EXIST"})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_path_with_no_telemetry_returns_empty_coordinates(self):
        #this test checks that when we access the path endpoint for a drone that exists in the database but has no associated telemetry records,
        #we get a valid GeoJSON response with an empty LineString geometry, indicating that there is no path data to return for that drone, 
        #but the endpoint is still functioning correctly and returning a valid response format
        Drone.objects.create(serial="EMPTY1")
        url = reverse("drone-path-geojson", kwargs={"serial": "EMPTY1"})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        body = res.json()
        self.assertEqual(body["geometry"]["type"], "LineString")
        self.assertEqual(body["geometry"]["coordinates"], [])
        self.assertEqual(body["properties"]["count"], 0)


class UtilsUnitTests(SimpleTestCase):
    def test_haversine_zero_distance(self):
        #this test checks that the haversine_km function correctly calculates a distance of 0 kilometers when the input coordinates are the same ex. the distance between a point and itself should be zero
        self.assertAlmostEqual(haversine_km(0, 0, 0, 0), 0.0, places=6)

    def test_haversine_known_distance_approx(self):
        #this test checks that the haversine_km function correctly calculates the distance between two points with known coordinates, 
        # and that the calculated distance is approximately equal to the expected distance within a reasonable margin of error, 
        # since the haversine formula provides an approximation of the distance between two points on the Earth's surface, 
        # and the actual distance may vary slightly due to factors such as the Earth's curvature and the specific coordinates used in the test
        # Roughly 111.19 km per 1 degree longitude at equator
        d = haversine_km(0, 0, 0, 1)
        self.assertTrue(110 < d < 112)


class StrategyUnitTests(SimpleTestCase):
    def test_default_classifier_not_dangerous_on_exact_threshold(self):
        #this test checks that the default_classifier's classify method returns an empty list of reasons (indicating that the drone is not considered dangerous) 
        # when the height is exactly 500 meters and the horizontal speed is exactly 10 m/s,
        #since the danger classification logic should only classify a drone as dangerous if the height exceeds 500 meters 
        # or the horizontal speed exceeds 10 m/s, not if they are exactly at the threshold values
        classifier = default_classifier()
        reasons = classifier.classify(height_m=500, horizontal_speed_mps=10)
        self.assertEqual(reasons, [])

    def test_default_classifier_returns_reasons_above_threshold(self):
        #this test checks that the default_classifier's classify method returns a non-empty list of reasons (indicating that the drone is considered dangerous)
        # when the height is above 500 meters and the horizontal speed is above 10 m/s, since the danger classification logic should classify 
        # a drone as dangerous if either the height exceeds 500 meters or the horizontal speed exceeds 10 m/s, and should provide appropriate reasons 
        # for why the drone is considered dangerous based on which thresholds were exceeded
        classifier = default_classifier()
        reasons = classifier.classify(height_m=600, horizontal_speed_mps=12)
        self.assertTrue(len(reasons) >= 1)