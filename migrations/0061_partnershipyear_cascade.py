# Generated by Django 2.2.10 on 2020-06-03 09:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('partnership', '0060_agreement_dates'),
    ]

    operations = [
        migrations.AlterField(
            model_name='partnershipyear',
            name='partnership',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='years', to='partnership.Partnership', verbose_name='partnership'),
        ),
    ]
