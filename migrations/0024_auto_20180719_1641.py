# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-07-19 14:41
from __future__ import unicode_literals

import datetime

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('partnership', '0023_partnershipconfiguration'),
    ]

    operations = [
        migrations.AlterField(
            model_name='partnership',
            name='start_date',
            field=models.DateField(default=datetime.date(2018, 1, 1), verbose_name='start_date'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='partnershipconfiguration',
            name='partnership_update_max_date_day',
            field=models.IntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10), (11, 11), (12, 12), (13, 13), (14, 14), (15, 15), (16, 16), (17, 17), (18, 18), (19, 19), (20, 20), (21, 21), (22, 22), (23, 23), (24, 24), (25, 25), (26, 26), (27, 27), (28, 28), (29, 29), (30, 30), (31, 31)], default=1, help_text='partnership_update_max_date_day_help_text', verbose_name='partnership_update_max_date_day'),
        ),
    ]
