# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-07-04 15:27
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0295_auto_20180627_1417'),
        ('partnership', '0009_auto_20180704_1058'),
    ]

    operations = [
        migrations.CreateModel(
            name='PartnershipAgreement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('waiting', 'status_waiting'), ('validated', 'status_validated'), ('refused', 'status_refused')], default='waiting', max_length=10, verbose_name='status')),
                ('note', models.TextField(blank=True, default='', verbose_name='note')),
                ('end_academic_year', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to='base.AcademicYear', verbose_name='end_academic_year')),
                ('media', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to='partnership.Media', verbose_name='media')),
                ('partnership', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='agreements', to='partnership.Partnership', verbose_name='partnership')),
                ('start_academic_year', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to='base.AcademicYear', verbose_name='start_academic_year')),
            ],
        ),
        migrations.RemoveField(
            model_name='partnershipoffer',
            name='end_academic_year',
        ),
        migrations.RemoveField(
            model_name='partnershipoffer',
            name='media',
        ),
        migrations.RemoveField(
            model_name='partnershipoffer',
            name='partnership',
        ),
        migrations.RemoveField(
            model_name='partnershipoffer',
            name='start_academic_year',
        ),
        migrations.DeleteModel(
            name='PartnershipOffer',
        ),
    ]
