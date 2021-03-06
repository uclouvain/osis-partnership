# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-06-28 07:16
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0295_auto_20180627_1417'),
        ('partnership', '0003_auto_20180625_1009'),
    ]

    operations = [
        migrations.AddField(
            model_name='partnership',
            name='is_signed',
            field=models.BooleanField(default=False, verbose_name='is_signed'),
        ),
        migrations.AddField(
            model_name='partnership',
            name='university_offers',
            field=models.ManyToManyField(related_name='partnerships', to='base.EducationGroupYear', verbose_name='UCL offer'),
        ),
        migrations.AlterField(
            model_name='address',
            name='country',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='reference.Country', verbose_name='country'),
        ),
        migrations.AlterField(
            model_name='partner',
            name='contact_address',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='partners', to='partnership.Address', verbose_name='address'),
        ),
    ]
