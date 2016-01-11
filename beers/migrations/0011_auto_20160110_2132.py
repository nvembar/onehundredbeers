# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-01-11 02:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('beers', '0010_auto_20151230_1719'),
    ]

    operations = [
        migrations.AddField(
            model_name='beer',
            name='description',
            field=models.CharField(blank=True, default='', max_length=250, null=True),
        ),
        migrations.AddField(
            model_name='player',
            name='city',
            field=models.CharField(blank=True, default='', max_length=150),
        ),
    ]
