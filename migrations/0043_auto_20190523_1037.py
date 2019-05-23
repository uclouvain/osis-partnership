# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-05-23 10:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('partnership', '0042_partnership_medias'),
    ]

    operations = [
        migrations.AddField(
            model_name='uclmanagemententity',
            name='course_catalogue_text_en',
            field=models.TextField(blank=True, default='', verbose_name='course_catalogue_text_en'),
        ),
        migrations.AddField(
            model_name='uclmanagemententity',
            name='course_catalogue_text_fr',
            field=models.TextField(blank=True, default='', verbose_name='course_catalogue_text_fr'),
        ),
        migrations.AddField(
            model_name='uclmanagemententity',
            name='course_catalogue_url_en',
            field=models.URLField(blank=True, default='', verbose_name='course_catalogue_url_en'),
        ),
        migrations.AddField(
            model_name='uclmanagemententity',
            name='course_catalogue_url_fr',
            field=models.URLField(blank=True, default='', verbose_name='course_catalogue_url_fr'),
        ),
    ]
