# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-06-17 16:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('beers', '0018_auto_20170617_1246'),
    ]

    operations = [
        migrations.AddField(
            model_name='brewery',
            name='untappd_url',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='brewery',
            name='untappd_id',
            field=models.CharField(blank=True, max_length=25, null=True),
        ),
    ]
