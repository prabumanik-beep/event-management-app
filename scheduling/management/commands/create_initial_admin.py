from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = 'Creates an admin user non-interactively if it does not exist, using environment variables.'

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.environ.get('DJANGO_ADMIN_USERNAME')
        password = os.environ.get('DJANGO_ADMIN_PASSWORD')
        email = os.environ.get('DJANGO_ADMIN_EMAIL')

        if not all([username, password, email]):
            self.stdout.write(self.style.ERROR(
                'Missing environment variables: DJANGO_ADMIN_USERNAME, DJANGO_ADMIN_PASSWORD, DJANGO_ADMIN_EMAIL'
            ))
            return

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f'Successfully created superuser: {username}'))
        else:
            self.stdout.write(self.style.WARNING(f'Superuser "{username}" already exists.'))