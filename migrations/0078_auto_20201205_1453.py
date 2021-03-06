# Generated by Django 2.2.13 on 2020-12-05 14:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('partnership', '0077_partner_entity_entity'),
    ]

    operations = [
        migrations.AlterField(
            model_name='partnershipentitymanager',
            name='entity',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='base.Entity'),
        ),
        migrations.AlterField(
            model_name='partnershipentitymanager',
            name='person',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='base.Person'),
        ),
    ]
