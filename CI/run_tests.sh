#!/bin/sh

set -e

echo "========== Starting CI: running tests... =========="
cd ..
cd auth_service/

# Django settings for pytest-django
export DJANGO_SETTINGS_MODULE=core.settings.dev

# Run pytest
pytest -v

echo "========== CI: Tests finished =========="
