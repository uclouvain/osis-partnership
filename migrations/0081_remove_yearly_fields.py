# Generated by Django 2.2.13 on 2020-12-17 14:53
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('partnership', '0080_migrate_yearly_fields'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='partnershipyear',
            name='description',
        ),
        migrations.RemoveField(
            model_name='partnershipyear',
            name='id_number',
        ),
        migrations.RemoveField(
            model_name='partnershipyear',
            name='missions',
        ),
        migrations.RemoveField(
            model_name='partnershipyear',
            name='project_title',
        ),
        migrations.RemoveField(
            model_name='partnershipyear',
            name='subtype',
        ),
        migrations.RemoveField(
            model_name='partnershipyear',
            name='ucl_status',
        ),
    ]
