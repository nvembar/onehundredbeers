# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-02-18 20:27
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('beers', '0030_auto_20180218_1311'),
    ]

    operations = [
        migrations.CreateModel(
            name='Contest_Bonus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default=None, max_length=50)),
                ('description', models.CharField(blank=True, default='', max_length=250, null=True)),
                ('hash_tags', models.CharField(default='', help_text='Comma delimited strings without # symbols representing the list of tags will score this bonus', max_length=250)),
                ('point_value', models.IntegerField(default=1)),
                ('contest', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='beers.Contest')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='contest_bonus',
            unique_together=set([('contest', 'name')]),
        ),
    ]
