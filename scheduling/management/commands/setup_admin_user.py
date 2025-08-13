from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = 'Creates the admin user from environment variables if it does not exist, or updates the password if it does.'

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.environ.get('DJANGO_ADMIN_USERNAME')
        password = os.environ.get('DJANGO_ADMIN_PASSWORD')
        email = os.environ.get('DJANGO_ADMIN_EMAIL')

        if not all([username, password, email]):
            raise CommandError(
                'Missing environment variables: DJANGO_ADMIN_USERNAME, DJANGO_ADMIN_PASSWORD, DJANGO_ADMIN_EMAIL'
            )

        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email, 'is_staff': True, 'is_superuser': True}
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" did not exist. A new superuser has been created.'))
        else:
            self.stdout.write(self.style.WARNING(f'Superuser "{username}" already exists.'))

        self.stdout.write(f'Setting password for user "{username}"...')
        user.set_password(password)
        user.save()
        self.stdout.write(self.style.SUCCESS(f'Password for "{username}" has been set successfully.'))