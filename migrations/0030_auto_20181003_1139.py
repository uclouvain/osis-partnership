# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-10-03 11:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('partnership', '0029_auto_20180925_1617'),
    ]

    operations = [
        migrations.AddField(
            model_name='partnership',
            name='external_id',
            field=models.CharField(blank=True, help_text='to_synchronize_with_epc', max_length=255, null=True, unique=True, verbose_name='external_id'),
        ),
        migrations.AddField(
            model_name='partnershipagreement',
            name='changed',
            field=models.DateField(auto_now=True, verbose_name='changed'),
        ),
        migrations.AddField(
            model_name='partnershipagreement',
            name='external_id',
            field=models.CharField(blank=True, help_text='to_synchronize_with_epc', max_length=255, null=True, unique=True, verbose_name='external_id'),
        ),
        migrations.AlterField(
            model_name='partnershipyear',
            name='education_fields',
            field=models.ManyToManyField(to='partnership.PartnershipYearEducationField', verbose_name='partnership_year_education_fields'),
        ),
        migrations.AlterField(
            model_name='partnershipyear',
            name='education_levels',
            field=models.ManyToManyField(blank=True, to='partnership.PartnershipYearEducationLevel', verbose_name='partnership_year_education_levels'),
        ),
    ]
