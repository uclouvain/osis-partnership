# Generated by Django 2.2.10 on 2020-06-03 15:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('partnership', '0061_partnershipyear_cascade'),
    ]

    operations = [
        migrations.AddField(
            model_name='partnership',
            name='is_public',
            field=models.BooleanField(default=True, help_text='partnership_is_public_help_text', verbose_name='partnership_is_public'),
        ),
    ]
