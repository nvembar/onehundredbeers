# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2015-12-26 02:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('beers', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='beer',
            name='brewery_lat',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='beer',
            name='brewery_lon',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='beer',
            name='style',
            field=models.CharField(blank=True, default='', max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='beer',
            name='untappd_id',
            field=models.CharField(blank=True, max_length=25, null=True),
        ),
        migrations.AlterField(
            model_name='checkin',
            name='comment',
            field=models.CharField(blank=True, default='', max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='checkin',
            name='untappd_checkin',
            field=models.URLField(blank=True, max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='contest',
            name='beer_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='contest',
            name='user_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='player',
            name='personal_statement',
            field=models.CharField(blank=True, default='', max_length=150),
        ),
        migrations.AlterField(
            model_name='player',
            name='untappd_rss',
            field=models.URLField(blank=True, max_length=512, null=True),
        ),
    ]
