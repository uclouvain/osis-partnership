# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-06-07 13:10
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('partnership', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='partnerentity',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='childs', to='partnership.PartnerEntity', verbose_name='parent_entity'),
        ),
    ]
