# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-10-01 16:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('partnership', '0037_auto_20181001_1426'),
    ]

    operations = [
        migrations.AddField(
            model_name='partnership',
            name='contacts',
            field=models.ManyToManyField(blank=True, related_name='_partnership_contacts_+', to='partnership.Contact', verbose_name='contacts'),
        ),
    ]
