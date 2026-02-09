import json
import logging

import paho.mqtt.client as mqtt

from django.core.management.base import BaseCommand

from drones.telemetry_in_serializer import TelemetryInSerializer
from drones.services import ingest_telemetry

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run MQTT subscriber to ingest drone telemetry"

    def add_arguments(self, parser):
        parser.add_argument("--host", default="localhost")
        parser.add_argument("--port", type=int, default=1883)
        parser.add_argument("--topic", default="drones/telemetry/#")
        parser.add_argument("--username", default=None)
        parser.add_argument("--password", default=None)

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

                # Validate exactly like HTTP endpoint
                serializer = TelemetryInSerializer(data=data)
                serializer.is_valid(raise_exception=True)

                # Reuse shared business logic
                drone, telemetry = ingest_telemetry(serializer.validated_data)

                logger.info("Ingested telemetry: serial=%s drone_id=%s telemetry_id=%s",
                            drone.serial, drone.id, telemetry.id)

            except Exception as e:
                logger.exception("Failed to ingest message on topic %s: %s", msg.topic, e)

        client.on_connect = on_connect
        client.on_message = on_message

        self.stdout.write(self.style.WARNING("Starting MQTT loop... (Ctrl+C to stop)"))
        client.connect(host, port, keepalive=60)
        client.loop_forever()