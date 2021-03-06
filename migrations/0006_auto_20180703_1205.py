# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-07-03 10:05
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0295_auto_20180627_1417'),
        ('partnership', '0005_remove_partnership_is_signed'),
    ]

    operations = [
        migrations.CreateModel(
            name='PartnershipYear',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mobility_type', models.CharField(choices=[('SMS', 'mobility_type_sms'), ('SMP', 'mobility_type_smp'), ('STA', 'mobility_type_sta'), ('STT', 'mobility_type_stt'), ('NA', 'mobility_type_na')], max_length=255, verbose_name='mobility_type')),
                ('academic_year', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to='base.AcademicYear', verbose_name='academic_year')),
                ('partnership', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='years', to='partnership.Partnership', verbose_name='partnership')),
                ('partnership_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='partnerships', to='partnership.PartnershipType', verbose_name='partnership_type')),
            ],
        ),
        migrations.RemoveField(
            model_name='partnership',
            name='mobility_type',
        ),
        migrations.RemoveField(
            model_name='partnership',
            name='partnership_type',
        ),
    ]
