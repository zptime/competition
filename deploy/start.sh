#!/usr/bin/env bash
. /opt/virt/competition_v3/bin/activate
cd ..
gunicorn --config gunicorn.conf competition_v3.wsgi:application --daemon

