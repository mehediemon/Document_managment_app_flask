#!/bin/sh

# Check if the migrations directory exists
if [ ! -d "migrations" ]; then
  echo "Migrations folder not found. Running 'flask db init', 'flask db migrate', and 'flask db upgrade'."
  flask db init
  flask db migrate -m "initial"
  flask db upgrade
else
  echo "Migrations folder found. Running 'flask db upgrade'."
  flask db upgrade
fi

# Start the Gunicorn server
exec gunicorn --bind 0.0.0.0:5003 run:app
