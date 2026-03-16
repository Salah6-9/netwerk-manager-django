#!/bin/bash

echo "Installing Node dependencies..."
npm install

echo "Building Tailwind CSS..."
npm run build

echo "Collecting Django static files..."
python manage.py collectstatic --noinput

echo "Applying database migrations..."
python manage.py migrate

echo "Deployment steps completed."
