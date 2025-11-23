# Run Django tests in isolated environment (local CI)

set -e  # Exit immediately if a command fails
echo "Starting CI: running tests..."
cd ../auth

# Export settings (adjust if needed)
export DJANGO_SETTINGS_MODULE=auth_service.settings.dev

# Run migrations in test DB
python manage.py makemigrations --check --dry-run
python manage.py migrate --noinput

# Run tests with verbose output
python manage.py test --verbosity=2

echo "CI tests finished successfully!"