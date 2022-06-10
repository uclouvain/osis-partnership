# Generated by Django 3.2.12 on 2022-06-10 16:21

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('partnership', '0001_squashed_0092_copy_partner_address_to_new_version'),
    ]

    operations = [
        migrations.AlterField(
            model_name='partner',
            name='is_nonprofit',
            field=models.BooleanField(blank=True, null=True, verbose_name='is_nonprofit'),
        ),
        migrations.AlterField(
            model_name='partner',
            name='is_public',
            field=models.BooleanField(blank=True, null=True, verbose_name='is_public'),
        ),
        migrations.AlterField(
            model_name='partnershipentitymanager',
            name='scopes',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('GENERAL', 'Accord général de collaboration'), ('MOBILITY', 'Partenariat de mobilité'), ('COURSE', 'Partenariat de co-organisation de formation'), ('DOCTORATE', 'Partenariat de co-organisation de doctorat'), ('PROJECT', 'Projet financé')], max_length=200), blank=True, size=None),
        ),
        migrations.AlterField(
            model_name='partnershipsubtype',
            name='order',
            field=models.PositiveIntegerField(db_index=True, editable=False, verbose_name='order'),
        ),
    ]
