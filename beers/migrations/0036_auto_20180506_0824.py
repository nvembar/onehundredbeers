# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-05-06 12:24
from __future__ import unicode_literals

from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('beers', '0035_contest_beer_brewery_name'),
    ]

    operations = [
        migrations.RunSQL(
            """UPDATE beers_contest_beer cb
                  SET brewery_name = b.brewery
                 FROM beers_beer b
                WHERE cb.beer_id = b.id;""",
            "UPDATE beers_contest_beer SET brewery_name = '';")
    ]
