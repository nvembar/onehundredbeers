# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2015-12-26 21:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('beers', '0004_contest_creator'),
    ]

    operations = [
        migrations.AddField(
            model_name='contest_player',
            name='rank',
            field=models.IntegerField(default=0),
        ),
    ]
