# Generated by Django 2.2.10 on 2020-06-10 15:27

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('base', '0540_prevent_empty_address'),
        ('partnership', '0065_sync_dates_years_agreements'),
    ]

    operations = [
        migrations.AddField(
            model_name='partner',
            name='organization',
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='base.Organization',
            ),
        ),
        migrations.AlterField(
            model_name='partner',
            name='website',
            field=models.URLField(verbose_name='website', null=True),
        ),
        migrations.AlterField(
            model_name='partner',
            name='name',
            field=models.CharField(max_length=255, verbose_name='name',
                                   null=True),
        ),
        migrations.AlterField(
            model_name='partner',
            name='partner_code',
            field=models.CharField(max_length=255, unique=True,
                                   verbose_name='partner_code', null=True),
        ),
        migrations.AlterField(
            model_name='partner',
            name='partner_type',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='partners',
                to='partnership.PartnerType',
                verbose_name='partner_type',
                null=True,
            ),
        ),
    ]
