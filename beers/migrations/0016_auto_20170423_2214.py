# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-24 02:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('beers', '0015_auto_20160123_1621'),
    ]

    operations = [
        migrations.AddField(
            model_name='contest_beer',
            name='point_value',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='contest_player',
            name='beer_points',
            field=models.IntegerField(default=0),
        ),
    ]
