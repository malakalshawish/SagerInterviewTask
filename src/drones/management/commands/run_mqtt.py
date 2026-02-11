import json
import logging
import os
import re

import paho.mqtt.client as mqtt
from django.core.management.base import BaseCommand

from drones.telemetry_in_serializer import TelemetryInSerializer
from drones.services import ingest_telemetry

logger = logging.getLogger(__name__)

import os
class Command(BaseCommand):
    help = "Run MQTT subscriber to ingest drone telemetry"

    def add_arguments(self, parser):
        parser.add_argument("--host", default=os.getenv("MQTT_HOST", "localhost"))
        parser.add_argument("--port", type=int, default=int(os.getenv("MQTT_PORT", "1883")))
        parser.add_argument("--topic", default=os.getenv("MQTT_TOPIC", "thing/product/+/osd"))
        parser.add_argument("--username", default=os.getenv("MQTT_USERNAME") or None)
        parser.add_argument("--password", default=os.getenv("MQTT_PASSWORD") or None)

    def handle(self, *args, **options):
        host = options["host"]
        port = options["port"]
        topic = options["topic"]
        username = options["username"]
        password = options["password"]

        client = mqtt.Client()

        if username and password:
            client.username_pw_set(username, password)

        def on_connect(client, userdata, flags, rc):
            self.stdout.write(self.style.SUCCESS(f"Connected to MQTT broker {host}:{port}, rc={rc}"))
            client.subscribe(topic)
            self.stdout.write(self.style.SUCCESS(f"Subscribed to topic: {topic}"))

        def on_message(client, userdata, msg):
            try:
                payload = msg.payload.decode("utf-8")
                data = json.loads(payload)

                # If publisher doesn't include serial in payload, extract from topic:
                # thing/product/{serial}/osd
                if "serial" not in data:
                    m = re.match(r"^thing/product/(?P<serial>[^/]+)/osd$", msg.topic)
                    if m:
                        data["serial"] = m.group("serial")

                # Validate exactly like HTTP endpoint
                serializer = TelemetryInSerializer(data=data)
                serializer.is_valid(raise_exception=True)

                # Reuse shared business logic
                drone, telemetry = ingest_telemetry(serializer.validated_data)

                # Make success visible to testers in terminal
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Ingested telemetry: serial={drone.serial} telemetry_id={telemetry.id}"
                    )
                )

                logger.info(
                    "Ingested telemetry: serial=%s drone_id=%s telemetry_id=%s",
                    drone.serial, drone.id, telemetry.id
                )

            except Exception as e:
                logger.exception("Failed to ingest message on topic %s: %s", msg.topic, e)

        client.on_connect = on_connect
        client.on_message = on_message

        self.stdout.write(self.style.WARNING("Starting MQTT loop... (Ctrl+C to stop)"))
        client.connect(host, port, keepalive=60)
        client.loop_forever()