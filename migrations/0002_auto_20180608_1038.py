# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-06-08 08:38
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('partnership', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='partnership',
            old_name='partner_type',
            new_name='partnership_type',
        ),
        migrations.AlterField(
            model_name='partnership',
            name='ucl_university_labo',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='base.EntityVersion', verbose_name='partner_entity'),
        ),
    ]