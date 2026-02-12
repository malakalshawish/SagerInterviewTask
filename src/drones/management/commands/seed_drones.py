import random
import string
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from drones.models import Drone


def random_serial(prefix="RAIL", length=10) -> str:
    chars = string.ascii_uppercase + string.digits
    return f"{prefix}-" + "".join(random.choice(chars) for _ in range(length))


def random_lat_lng():
    lat = random.uniform(24.8, 25.4)
    lng = random.uniform(54.8, 55.6)
    return lat, lng


class Command(BaseCommand):
    help = "Seed drones into Railway DB and print local+railway totals."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=100)
        parser.add_argument("--prefix", type=str, default="RAIL")

    @transaction.atomic
    def handle(self, *args, **options):
        count = options["count"]
        prefix = options["prefix"]

        if "railway" not in settings.DATABASES:
            self.stderr.write("Railway DB alias not configured. Set RAILWAY_DATABASE_URL.")
            return

        # Counts before
        local_before = Drone.objects.count()
        railway_before = Drone.objects.using("railway").count()

        # Avoid duplicate serials on Railway
        existing_serials = set(
            Drone.objects.using("railway")
            .filter(serial__startswith=f"{prefix}-")
            .values_list("serial", flat=True)
        )

        danger_reason_pool = [
            "entered_geofence",
            "altitude_spike",
            "speed_spike",
            "gps_jitter",
            "unknown_serial_pattern",
        ]

        drones_to_create = []
        created_serials = []  #track serials we attempt to create
        attempts = 0

        while len(drones_to_create) < count:
            attempts += 1
            if attempts > count * 50:
                raise RuntimeError("Too many collisions generating unique serials.")

            serial = random_serial(prefix=prefix, length=10)
            if serial in existing_serials:
                continue
            existing_serials.add(serial)
            created_serials.append(serial)  #track for later printing

            lat, lng = random_lat_lng()
            is_dangerous = random.random() < 0.2

            danger_reasons = []
            if is_dangerous:
                danger_reasons = random.sample(
                    danger_reason_pool, k=random.randint(1, min(3, len(danger_reason_pool)))
                )

            drones_to_create.append(
                Drone(
                    serial=serial,
                    last_seen=timezone.now() if random.random() < 0.9 else None,
                    last_lat=lat if random.random() < 0.9 else None,
                    last_lng=lng if random.random() < 0.9 else None,
                    is_dangerous=is_dangerous,
                    danger_reasons=danger_reasons,
                )
            )

        # Seed into Railway only
        Drone.objects.using("railway").bulk_create(drones_to_create, ignore_conflicts=True)

        #Print first 10 newest rows that match the serials we just generated
        new_rows = (
            Drone.objects.using("railway")
            .filter(serial__in=created_serials)
            .order_by("-id")
            .values("id", "serial", "is_dangerous", "last_seen", "last_lat", "last_lng")[:10]
        )

        self.stdout.write("First 10 new drones (Railway):")
        for row in new_rows:
            self.stdout.write(
                f"  id={row['id']} serial={row['serial']} "
                f"danger={row['is_dangerous']} last_seen={row['last_seen']} "
                f"lat={row['last_lat']} lng={row['last_lng']}"
            )

        # Counts after
        local_after = Drone.objects.count()
        railway_after = Drone.objects.using("railway").count()

        created_on_railway = railway_after - railway_before

        default_db = settings.DATABASES["default"]
        railway_db = settings.DATABASES["railway"]

        self.stdout.write(
            "DB targets:\n"
            f"  default -> {default_db.get('HOST')}:{default_db.get('PORT')}\n"
            f"  railway  -> {railway_db.get('HOST')}:{railway_db.get('PORT')}\n"
        )

        self.stdout.write(self.style.SUCCESS(
            "Seed complete\n"
            f"Railway created (actual): {created_on_railway}\n"
            f"Railway total: {railway_before} → {railway_after}\n"
            f"Local total:   {local_before} → {local_after}"
        ))