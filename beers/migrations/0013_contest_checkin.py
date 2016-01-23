# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-01-19 03:36
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('beers', '0012_player_untappd_username'),
    ]

    operations = [
        migrations.CreateModel(
            name='Contest_Checkin',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('checkin_time', models.DateTimeField()),
                ('untappd_checkin', models.URLField(blank=True, max_length=250, null=True)),
                ('contest_beer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='beers.Contest_Beer')),
                ('contest_player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='beers.Contest_Player')),
            ],
        ),
    ]
