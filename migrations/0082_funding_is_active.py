# Generated by Django 2.2.13 on 2020-12-18 11:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('partnership', '0081_remove_yearly_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='fundingprogram',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='is_active'),
        ),
        migrations.AddField(
            model_name='fundingtype',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='is_active'),
        ),
    ]
