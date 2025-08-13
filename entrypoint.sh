#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

echo "--- [1/5] Starting deployment script ---"

echo "--- [2/5] Running database migrations ---"
python manage.py migrate
echo "--- Migrations complete ---"

echo "--- [3/5] Collecting static files ---"
python manage.py collectstatic --noinput
echo "--- Static files collected ---"

echo "--- [4/5] Ensuring admin user exists ---"
python manage.py setup_admin_user
echo "--- Admin user setup complete ---"

echo "--- [5/5] Generating one-time login token ---"
python manage.py generate_login_token
echo "--- Login token generated ---"

echo "--- Starting Gunicorn server ---"
# Use the PORT environment variable provided by Render, defaulting to 10000.
# Bind to 0.0.0.0 to be accessible from outside the container.
exec gunicorn event_management.wsgi:application --bind "0.0.0.0:${PORT:-10000}"