#!/usr/bin/env bash
# build.sh — Render ejecuta este script automáticamente antes de publicar.
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate
