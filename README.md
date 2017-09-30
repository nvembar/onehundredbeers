### Build instructions

This uses Python 3.6, so make sure that's installed. To set up your own virtual environment, follow the directions below.

If you don't have it, get bower:
```
$ npm install -g bower
```

Create a Postgres database and point to it using the environment variable `DATABASE_URL`. Create a Django secret key and store it in `SECRET_KEY`.

Generally, if you're running this in test, set `SSL_REDIRECT=0` so that Django doesn't redirect on your local machine.

```
$ virtualenv hundred_beers
$ cd hundred_beers
$ git clone [hundred_beers repo]
$ pip install
$ python manage.py bower install
$ python manage.py collectstatic
$ python manage.py makemigrations
$ python manage.py migrate
$ python manage.py runserver
```

The project is set to be deployed in Heroku.

#### Run with Docker

Alternatively, you can run this in Docker with `docker-compose up`. You will need to set `SECRET_KEY` as an environment variable before running the command. If it's the first time setting it up,
`docker-compose run web python3 manage.py migrate` will create an empty database.
