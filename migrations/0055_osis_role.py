# Generated by Django 2.2.10 on 2020-05-14 17:13
import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('partnership', '0054_move_partnership_type'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='partnershipentitymanager',
            options={'verbose_name': 'Partnership manager', 'verbose_name_plural': 'Partnership managers'},
        ),
        migrations.AddField(
            model_name='partnershipentitymanager',
            name='with_child',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='partnershipentitymanager',
            name='with_child',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='partnershipentitymanager',
            name='scopes',
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(
                    choices=[
                        ('GENERAL', 'Accord général de collaboration'),
                        ('MOBILITY', 'Partenariat de mobilité'),
                        ('COURSE',
                         'Partenariat de co-organisation de formation'),
                        ('DOCTORATE',
                         'Partenariat de co-organisation de doctorat'),
                        ('PROJECT', 'Projet financé'),
                    ], max_length=200),
                blank=True, default=['MOBILITY'], size=None),
            preserve_default=False,
        ),
    ]
