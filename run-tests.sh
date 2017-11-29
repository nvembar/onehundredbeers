#!/bin/bash

python3 manage.py collectstatic --noinput
python3 manage.py test
