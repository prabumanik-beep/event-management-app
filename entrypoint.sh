#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

echo "--- Running database migrations ---"
python manage.py migrate

echo "--- Collecting static files ---"
python manage.py collectstatic --noinput

echo "--- Creating initial admin user (if it doesn't exist) ---"
python manage.py create_initial_admin

echo "--- Starting Gunicorn server ---"
exec gunicorn event_management.wsgi:application