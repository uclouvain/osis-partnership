# Generated by Django 2.2.13 on 2020-07-13 17:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('partnership', '0069_funding_hierarchy_year'),
    ]

    operations = [
        migrations.AlterField(
            model_name='partnership',
            name='comment',
            field=models.TextField(blank=True, default='', help_text='invisible_on_api', verbose_name='comment'),
        ),
        migrations.AlterField(
            model_name='partnershipyear',
            name='description',
            field=models.TextField(blank=True, default='', help_text='visible_on_api', verbose_name='partnership_year_description'),
        ),
    ]
