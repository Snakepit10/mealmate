#!/bin/sh
set -e

echo "Waiting for database..."
python -c "
import time, django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()
from django.db import connection
while True:
    try:
        connection.ensure_connection()
        break
    except Exception:
        time.sleep(1)
print('Database ready.')
"

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear 2>/dev/null || true

echo "Starting server..."
PORT="${PORT:-8000}"
exec daphne -b 0.0.0.0 -p "$PORT" config.asgi:application
