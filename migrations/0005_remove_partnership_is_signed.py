# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-06-28 12:28
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('partnership', '0004_auto_20180628_0916'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='partnership',
            name='is_signed',
        ),
    ]
