# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-07-31 14:01
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('partnership', '0026_auto_20180726_1129'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='partnershipagreement',
            options={'ordering': ['-start_academic_year__start_date']},
        ),
        migrations.AlterField(
            model_name='contact',
            name='title',
            field=models.CharField(blank=True, choices=[('mr', 'mister'), ('mme', 'madame')], max_length=50, null=True, verbose_name='contact_title'),
        ),
        migrations.AlterField(
            model_name='partnership',
            name='supervisor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='partnerships_supervisor', to='base.Person', verbose_name='partnership_supervisor'),
        ),
    ]