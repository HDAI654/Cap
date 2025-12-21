#!/bin/sh

echo "Waiting for Postgres..."

while ! nc -z auth-db 5432; do
  sleep 0.5
done

echo "Postgres is up!"

python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser --noinput || true

exec "$@"
