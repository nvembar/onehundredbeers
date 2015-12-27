# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2015-12-26 02:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('beers', '0002_auto_20151225_2116'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contest_player',
            name='last_checkin_beer',
            field=models.CharField(blank=True, max_length=250, null=True, verbose_name='Denormalized beer name from last checkin'),
        ),
        migrations.AlterField(
            model_name='contest_player',
            name='last_checkin_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Denormalized date from last checkin'),
        ),
    ]
