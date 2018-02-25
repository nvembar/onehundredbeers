#!/bin/bash

sleep 5
coverage run manage.py test
if [ ! -d coverage ]; then
    mkdir coverage
fi
coverage xml -o coverage/coverage.xml
