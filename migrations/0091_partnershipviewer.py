# Generated by Django 2.2.13 on 2021-05-03 15:15
from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Q


def forward(apps, schema_editor):
    Permission = apps.get_model('auth', 'Permission')
    Person = apps.get_model('base', 'Person')
    PartnershipViewer = apps.get_model('partnership', 'PartnershipViewer')

    # Get the perm and the persons having this perm
    perm = Permission.objects.get(codename='can_access_partnerships')
    persons = Person.objects.filter(Q(user__groups__permissions=perm) | Q(user__user_permissions=perm)).distinct()

    instances = [PartnershipViewer(person=p) for p in persons]
    PartnershipViewer.objects.bulk_create(instances)


class Migration(migrations.Migration):
    dependencies = [
        ('base', '0583_auto_20210324_0954'),
        ('partnership', '0090_remove_partner_is_ies'),
    ]

    operations = [
        migrations.CreateModel(
            name='PartnershipViewer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('person', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='+',
                    to='base.Person',
                )),
            ],
            options={
                'verbose_name': 'Partnership viewer',
                'verbose_name_plural': 'Partnership viewers',
            },
        ),
        migrations.RunPython(forward, migrations.RunPython.noop)
    ]
