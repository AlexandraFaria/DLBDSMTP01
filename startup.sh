#!/bin/bash
apt-get update
apt-get install -y msodbcsql18  # Adjust if needed for your ODBC version
gunicorn -b 0.0.0.0:8000 app:app  # Adjust if your file name is different
