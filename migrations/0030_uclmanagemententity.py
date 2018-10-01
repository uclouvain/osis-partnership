# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-09-24 15:32
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0332_auto_20180816_1540'),
        ('partnership', '0029_auto_20180809_1128'),
    ]

    operations = [
        migrations.CreateModel(
            name='UCLManagementEntity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('academic_respondent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='base.Person')),
                ('administrative_responsible', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.Person')),
                ('contact_in', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='partnership.Contact')),
                ('contact_out', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='partnership.Contact')),
                ('entity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.Entity')),
                ('faculty', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.EntityVersion')),
            ],
        ),
    ]
