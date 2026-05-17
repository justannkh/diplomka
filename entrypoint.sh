#!/bin/bash
set -e

cd project

echo "=== Collecting static files ==="
python manage.py collectstatic --noinput

echo "=== Applying migrations ==="
python manage.py migrate --noinput

echo "=== Creating superuser (if not exists) ==="
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='Ankh').exists() or User.objects.create_superuser('Ankh', 'admin@example.com', '123503623ANKh')" | python manage.py shell

echo "=== Starting Gunicorn ==="
exec gunicorn beverage_store.wsgi:application --bind 0.0.0.0:${PORT:-8000}
