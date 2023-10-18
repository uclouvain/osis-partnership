# Generated by Django 3.2.21 on 2023-10-11 16:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('partnership', '0003_auto_20220922_1004'),
    ]

    operations = [
        migrations.AddField(
            model_name='partner',
            name='organisation_identifier',
            field=models.CharField(blank=True, max_length=255, null=True, unique=True, verbose_name='organisation_identifier'),
        ),
        migrations.AddField(
            model_name='partner',
            name='size',
            field=models.CharField(blank=True, choices=[('>250', 'partner_size_gt_250'), ('<250', 'partner_size_lt_250')], max_length=255, null=True, verbose_name='partner_size'),
        ),
    ]
