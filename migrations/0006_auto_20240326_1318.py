# Generated by Django 3.2.25 on 2024-03-26 13:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('partnership', '0005_auto_20231019_1634'),
    ]

    operations = [
        migrations.AddField(
            model_name='partnershipentitymanager',
            name='visible',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='partnershipviewer',
            name='visible',
            field=models.BooleanField(default=True),
        ),
    ]
