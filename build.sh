#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

cd project

python manage.py collectstatic --noinput
python manage.py migrate --noinput

echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='Ankh').exists() or User.objects.create_superuser('Ankh', 'admin@example.com', '123503623ANKh')" | python manage.py shell
