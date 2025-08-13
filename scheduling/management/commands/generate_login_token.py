from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
import os
from rest_framework_simplejwt.tokens import RefreshToken

class Command(BaseCommand):
    help = 'Generates a JWT access and refresh token for the admin user.'

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.environ.get('DJANGO_ADMIN_USERNAME')

        if not username:
            raise CommandError('Missing environment variable: DJANGO_ADMIN_USERNAME')

        try:
            user = User.objects.get(username=username)
            refresh = RefreshToken.for_user(user)

            self.stdout.write(self.style.SUCCESS('\n--- ONE-TIME LOGIN TOKENS ---'))
            self.stdout.write('Copy these tokens from the log to log in via your browser developer tools.')
            self.stdout.write(self.style.WARNING(f'access_token: {str(refresh.access_token)}'))
            self.stdout.write(self.style.WARNING(f'refresh_token: {str(refresh)}'))
            self.stdout.write('---------------------------------\n')

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Superuser "{username}" does not exist. The setup_admin_user script may have failed.'))