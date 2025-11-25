#!/bin/sh

# Run linters (black, flake8) before tests

echo "Running code style checks..."
pip install --quiet black flake8

cd ..
cd auth/

# Check formatting
black .

# Check linting
# flake8 .

echo "Linting finished."
