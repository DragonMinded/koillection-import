set positional-arguments

# Set up virtual environment and dependencies
setup:
    python3 -m venv .venv
    ./.venv/bin/python3 -m pip install --upgrade pip -r requirements.txt

# Build everything that needs to be built and then run critterchat using config from init
run *ARGS:
    ./.venv/bin/python3 import.py "$@"

# Run all frontend and backend linting tools
lint:
    ./.venv/bin/flake8 .
    ./.venv/bin/mypy .
