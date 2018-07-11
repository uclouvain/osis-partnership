# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-07-11 09:40
from __future__ import unicode_literals

from django.db import migrations, models


def migrate_entities(apps, schema_editor):
    PartnershipYear = apps.get_model('partnership', 'PartnershipYear')
    PartnershipYear.objects.update(partnership_type='mobility')


class Migration(migrations.Migration):

    dependencies = [
        ('partnership', '0018_auto_20180711_1045'),
    ]

    operations = [
        migrations.AlterField(
            model_name='partnershipyear',
            name='partnership_type',
            field=models.CharField(choices=[('intention', 'Déclaration d’intention'), ('cadre', 'Accord-cadre'), ('specifique', 'Accord spécifique'), ('codiplomation', 'Accord de co-diplômation'), ('cotutelle', 'Accord de co-tutelle'), ('mobility', 'Partenariat de mobilité'), ('fond_appuie', 'Projet Fonds d’appuie à l’internationnalisation'), ('autre', 'Autre')], max_length=255, verbose_name='partnership_type'),
        ),
        migrations.DeleteModel(
            name='PartnershipType',
        ),
        migrations.RunPython(migrate_entities),
    ]