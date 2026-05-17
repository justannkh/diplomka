#!/bin/bash

cd project

echo "=== Collecting static files ==="
python manage.py collectstatic --noinput

echo "=== Applying migrations ==="
python manage.py migrate --noinput

echo "=== Creating superuser ==="
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beverage_store.settings')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='Ankh').exists():
    User.objects.create_superuser('Ankh', 'admin@example.com', '123503623ANKh')
    print('Superuser Ankh created')
else:
    print('Superuser Ankh already exists')
"

echo "=== Populating database with products ==="
python populate_data.py

echo "=== Starting Gunicorn ==="
exec gunicorn beverage_store.wsgi:application --bind 0.0.0.0:${PORT:-8000}
