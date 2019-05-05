#!/bin/bash

sleep 5
pipenv run coverage run manage.py test
if [ ! -d coverage ]; then
    mkdir coverage
fi
pipenv run coverage xml -o coverage/coverage.xml
