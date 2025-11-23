# Run linters (black, flake8) before tests

echo "Running code style checks..."
pip install --quiet black flake8

# Check formatting
black --check .

# Check linting
flake8 .

echo "Linting finished."
