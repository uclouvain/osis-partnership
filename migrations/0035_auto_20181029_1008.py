# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-10-29 10:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0376_auto_20181022_1510'),
        ('partnership', '0034_partnershipconfiguration_email_notification_to'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='partnership',
            options={'ordering': ('-created',), 'permissions': (('can_access_partnerships', 'can_access_partnerships'),)},
        ),
        migrations.AlterField(
            model_name='media',
            name='file',
            field=models.FileField(blank=True, help_text='media_file_or_url', null=True, upload_to='partnerships/', verbose_name='file'),
        ),
        migrations.AlterUniqueTogether(
            name='financing',
            unique_together=set([('name', 'academic_year')]),
        ),
    ]
