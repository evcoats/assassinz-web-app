#!/bin/bash

source /var/app/venv/staging-LQM1lest/bin/activate
cd /var/app/staging

python manage.py makemigrations
python manage.py migrate
python manage.py createsu
