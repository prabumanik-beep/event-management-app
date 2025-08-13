#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

echo "--- Running database migrations ---"
python manage.py migrate

echo "--- Collecting static files ---"
python manage.py collectstatic --noinput

echo "--- Ensuring admin user exists ---"
python manage.py setup_admin_user # This ensures the user is there

echo "--- Generating one-time login token ---"
python manage.py generate_login_token # This generates the token for login

echo "--- Starting Gunicorn server ---"
# Use the PORT environment variable provided by Render, defaulting to 10000.
# Bind to 0.0.0.0 to be accessible from outside the container.
exec gunicorn event_management.wsgi:application --bind "0.0.0.0:${PORT:-10000}"