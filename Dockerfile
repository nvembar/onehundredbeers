FROM python:3
ARG SECRET_KEY
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code
RUN SECRET_KEY=$SECRET_KEY python manage.py collectstatic --noinput
