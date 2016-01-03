### Build instructions

This uses Python 3.5, so make sure that's installed. To set up your own virtual environment, follow the directions below.

If you don't have it, get bower:
```
$ npm install -g bower 
```

Create a Postgres database and point to it using `DATABASE_URL`

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


