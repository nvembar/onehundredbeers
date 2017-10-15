FROM python:3
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY beers /code/
COPY hundred_beers /code/
COPY manage.py /code/
COPY Procfile /code/
COPY runtime.txt /code/
