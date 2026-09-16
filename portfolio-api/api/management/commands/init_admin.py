import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Create admin superuser from environment variables if none exists'

    def handle(self, *args, **options):
        username = os.environ.get('ADMIN_USERNAME', 'Christopher')
        email = os.environ.get('ADMIN_EMAIL', 'curlsjamin@gmail.com')
        password = os.environ.get('ADMIN_PASSWORD', '')

        if not password:
            self.stdout.write(self.style.WARNING('ADMIN_PASSWORD not set, skipping'))
            return

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" created'))
        else:
            self.stdout.write(f'Superuser "{username}" already exists')
