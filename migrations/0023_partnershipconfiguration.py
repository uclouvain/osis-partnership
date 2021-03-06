# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-07-19 14:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('partnership', '0022_auto_20180717_1504'),
    ]

    operations = [
        migrations.CreateModel(
            name='PartnershipConfiguration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('partnership_creation_max_date_day', models.IntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10), (11, 11), (12, 12), (13, 13), (14, 14), (15, 15), (16, 16), (17, 17), (18, 18), (19, 19), (20, 20), (21, 21), (22, 22), (23, 23), (24, 24), (25, 25), (26, 26), (27, 27), (28, 28), (29, 29), (30, 30), (31, 31)], default=31, help_text='partnership_creation_max_date_day_help_text', verbose_name='partnership_creation_max_date_day')),
                ('partnership_creation_max_date_month', models.IntegerField(choices=[(1, 'january'), (2, 'february'), (3, 'march'), (4, 'april'), (5, 'may'), (6, 'june'), (7, 'july'), (8, 'august'), (9, 'september'), (10, 'october'), (11, 'november'), (12, 'december')], default=12, help_text='partnership_creation_max_date_month_help_text', verbose_name='partnership_creation_max_date_month')),
                ('partnership_update_max_date_day', models.IntegerField(default=1, help_text='partnership_update_max_date_day_help_text', verbose_name='partnership_update_max_date_day')),
                ('partnership_update_max_date_month', models.IntegerField(choices=[(1, 'january'), (2, 'february'), (3, 'march'), (4, 'april'), (5, 'may'), (6, 'june'), (7, 'july'), (8, 'august'), (9, 'september'), (10, 'october'), (11, 'november'), (12, 'december')], default=3, help_text='partnership_update_max_date_month_help_text', verbose_name='partnership_update_max_date_month')),
            ],
        ),
    ]
