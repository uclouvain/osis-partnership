# Generated by Django 2.2.10 on 2020-05-19 16:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('partnership', '0057_fundings'),
    ]

    operations = [
        migrations.AddField(
            model_name='partnership',
            name='end_date',
            field=models.DateField(null=True, verbose_name='end_date'),
        ),
        migrations.AddField(
            model_name='partnership',
            name='start_date',
            field=models.DateField(null=True, verbose_name='start_date'),
        ),
    ]
