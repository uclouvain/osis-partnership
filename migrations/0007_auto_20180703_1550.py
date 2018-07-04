# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-07-03 13:50
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0295_auto_20180627_1417'),
        ('partnership', '0006_auto_20180703_1205'),
    ]

    operations = [
        migrations.CreateModel(
            name='PartnershipOffer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('state', models.CharField(choices=[('waiting', 'state_waiting'), ('validated', 'state_validated'), ('refused', 'state_refused')], default='waiting', max_length=10, verbose_name='state')),
                ('note', models.TextField(blank=True, default='', verbose_name='note')),
                ('end_academic_year', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to='base.AcademicYear', verbose_name='end_academic_year')),
                ('media', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to='partnership.Media', verbose_name='media')),
            ],
        ),
        migrations.AlterField(
            model_name='partnership',
            name='ucl_university',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='partnerships', to='base.EntityVersion', verbose_name='ucl_university'),
        ),
        migrations.AlterField(
            model_name='partnership',
            name='ucl_university_labo',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='partnerships_labo', to='base.EntityVersion', verbose_name='ucl_university_labo'),
        ),
        migrations.AlterField(
            model_name='partnership',
            name='university_offers',
            field=models.ManyToManyField(related_name='partnerships', to='base.EducationGroupYear', verbose_name='university_offers'),
        ),
        migrations.AddField(
            model_name='partnershipoffer',
            name='partnership',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='offers', to='partnership.Partnership', verbose_name='partnership'),
        ),
        migrations.AddField(
            model_name='partnershipoffer',
            name='start_academic_year',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to='base.AcademicYear', verbose_name='start_academic_year'),
        ),
    ]