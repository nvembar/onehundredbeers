#!/bin/bash

sleep 5
coverage run manage.py test
mkdir coverage
cp .coverage coverage
