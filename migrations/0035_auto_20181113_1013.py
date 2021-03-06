# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-11-13 10:13
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0383_organizationaddress_is_main'),
        ('partnership', '0034_partnershipconfiguration_email_notification_to'),
    ]

    operations = [
        migrations.CreateModel(
            name='PartnershipEntityManager',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('entity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.Entity')),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.Person')),
            ],
        ),
    ]
