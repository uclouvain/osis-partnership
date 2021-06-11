# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-06-25 08:09
from __future__ import unicode_literals

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def set_medias_author(apps, schema_editor):
    Media = apps.get_model('partnership', 'Media')
    User = apps.get_model('auth', 'User')
    Media.objects.update(author=User.objects.first())


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('partnership', '0002_auto_20180608_1038'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='media',
            name='document_file',
        ),
        migrations.AddField(
            model_name='media',
            name='author',
            field=models.ForeignKey(null=True, editable=False, on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='author'),
            preserve_default=False,
        ),
        migrations.RunPython(set_medias_author, reverse_code=migrations.RunPython.noop, elidable=True),
        migrations.AlterField(
            model_name='media',
            name='author',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='author'),
        ),
        migrations.AddField(
            model_name='media',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to='medias/', verbose_name='file'),
        ),
        migrations.AlterField(
            model_name='address',
            name='country',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='reference.Country', verbose_name='country'),
        ),
        migrations.AlterField(
            model_name='partner',
            name='contact_address',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='partners', to='partnership.Address', verbose_name='address'),
        ),
    ]
