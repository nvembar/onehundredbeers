FROM python:3
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code
RUN python3 manage.py collectstatic
