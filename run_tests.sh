#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Run Python tests
echo "Running Python tests..."
pytest

# Run R tests
echo "Running R tests..."
Rscript R/tests/run_tests.R
