# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-07-10 09:42
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('partnership', '0015_auto_20180710_1050'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='partnership',
            name='is_valid',
        ),
    ]
