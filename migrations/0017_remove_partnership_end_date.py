# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-07-10 10:00
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('partnership', '0016_remove_partnership_is_valid'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='partnership',
            name='end_date',
        ),
    ]
