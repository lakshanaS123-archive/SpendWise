import os
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from myapp.models import Budget, Transaction

User = get_user_model()


class Command(BaseCommand):
    help = "Safely and idempotently import initial user accounts, transactions, and budgets into PostgreSQL."

    def handle(self, *args, **options):
        # Check if initial users already exist in the database
        if User.objects.filter(username__in=["lakshana", "Lakshana_S"]).exists():
            self.stdout.write(
                self.style.SUCCESS(
                    "Initial user accounts already exist in the database. Skipping import to preserve data and avoid duplicates."
                )
            )
            return

        fixture_path = os.path.join(settings.BASE_DIR, "initial_data_backup.json")
        if not os.path.exists(fixture_path):
            self.stdout.write(
                self.style.WARNING(
                    f"Fixture {fixture_path} not found. Skipping initial data load."
                )
            )
            return

        self.stdout.write("Loading initial demonstration data (users, transactions, budgets)...")
        try:
            call_command("loaddata", fixture_path)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully loaded initial records! (Users: {User.objects.count()}, Transactions: {Transaction.objects.count()}, Budgets: {Budget.objects.count()})"
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error loading initial data: {e}")
            )
