# Generated by Django 3.2.25 on 2024-07-03 09:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('partnership', '0006_auto_20240326_1318'),
    ]

    operations = [
        migrations.AlterField(
            model_name='media',
            name='file',
            field=models.FileField(blank=True, help_text='media_file_or_url', null=True, upload_to='partnerships/', verbose_name='File'),
        ),
    ]
