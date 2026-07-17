#!/bin/sh
set -eu
exec gunicorn config.wsgi:application --config deploy/gunicorn.conf.py
