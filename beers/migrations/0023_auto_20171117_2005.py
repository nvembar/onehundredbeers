# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-11-18 01:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('beers', '0022_auto_20171117_1915'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contest_checkin',
            name='tx_type',
            field=models.CharField(choices=[('BE', 'Beer'), ('BR', 'Brewery'), ('CO', 'Challenge Beer - Other'), ('CS', 'Challenge Beer - Self'), ('CL', 'Challenge Beer - Loss'), ('BO', 'Bonus')], default='BE', max_length=2),
        ),
    ]
