from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = 'Finds the admin user specified by DJANGO_ADMIN_USERNAME and resets their password to DJANGO_ADMIN_PASSWORD.'

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.environ.get('DJANGO_ADMIN_USERNAME')
        password = os.environ.get('DJANGO_ADMIN_PASSWORD')

        if not username or not password:
            raise CommandError('Missing environment variables: DJANGO_ADMIN_USERNAME, DJANGO_ADMIN_PASSWORD')

        try:
            user = User.objects.get(username=username)
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Successfully reset password for superuser: {username}'))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Superuser "{username}" does not exist. The create_initial_admin script may have failed.'))