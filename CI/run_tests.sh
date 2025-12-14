#!/bin/sh

set -e

echo "========== Starting CI: running tests... =========="
cd ..
cd auth/

# Django settings for pytest-django
export DJANGO_SETTINGS_MODULE=auth_service.settings.dev

# Optional but recommended: ensure migrations are valid
python manage.py makemigrations --check --dry-run

# Run pytest
pytest -v

echo "========== CI: Tests finished =========="
