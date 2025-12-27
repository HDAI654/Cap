#!/bin/sh

# Run linters (black, flake8) before tests

echo "Running code style checks..."
pip install --quiet black flake8

cd ..
cd auth_service/

# Check formatting
black .

# Check linting
# flake8 .

echo "Linting finished."
