# Generated by Django 2.2.10 on 2020-04-06 15:59
from django.db import migrations, models
import django.db.models.deletion
from django.db.models import F, OuterRef, Subquery

from base.models.enums.entity_type import FACULTY


def forward(apps, schema_editor):
    UCLManagementEntity = apps.get_model('partnership', 'UCLManagementEntity')

    # Move faculty field to entity when entity is null
    UCLManagementEntity.objects.filter(
        entity__isnull=True,
    ).update(
        entity=F('faculty')
    )


def backward(apps, schema_editor):
    UCLManagementEntity = apps.get_model('partnership', 'UCLManagementEntity')
    EntityVersion = apps.get_model('base', 'EntityVersion')

    # Get faculty of entity when entity is a not faculty
    UCLManagementEntity.objects.annotate(
        entity_type=Subquery(EntityVersion.objects
            .filter(entity_id=OuterRef('entity_id'))
            .order_by('-start_date')
            .values('entity_type')[:1]),
        replacing_faculty_id=Subquery(EntityVersion.objects
            .filter(entity__parent_of__entity_id=OuterRef('entity_id'))
            .order_by('-start_date')
            .values('entity_id')[:1]),
    ).exclude(
        entity_type=FACULTY,
    ).update(
        faculty_id=F('replacing_faculty_id'),
    )

    # Move entity to faculty field when entity is a faculty
    UCLManagementEntity.objects.annotate(
        entity_type=Subquery(EntityVersion.objects
            .filter(entity=OuterRef('entity_id'))
            .order_by('-start_date')
            .values('entity_type')[:1]),
    ).filter(
        entity_type=FACULTY,
    ).update(
        faculty=F('entity'),
        entity=None,
    )


class Migration(migrations.Migration):
    dependencies = [
        ('partnership', '0050_configuration_academic_year'),
    ]

    operations = [
        migrations.AlterField(
            model_name='partnership',
            name='ucl_university',
            field=models.ForeignKey(limit_choices_to=models.Q(models.Q(entityversion__entity_type='FACULTY'), models.Q(('uclmanagement_entity__isnull', False), ('parent_of__entity__uclmanagement_entity__isnull', False), _connector='OR')), on_delete=django.db.models.deletion.PROTECT, related_name='partnerships', to='base.Entity', verbose_name='ucl_university'),
        ),
        migrations.AlterField(
            model_name='partnership',
            name='ucl_university_labo',
            field=models.ForeignKey(blank=True, limit_choices_to=models.Q(models.Q(entityversion__parent__entityversion__entity_type='FACULTY'), models.Q(('uclmanagement_entity__isnull', False), ('entityversion__parent__uclmanagement_entity__isnull', False), _connector='OR')), null=True, on_delete=django.db.models.deletion.PROTECT, related_name='partnerships_labo', to='base.Entity', verbose_name='ucl_university_labo'),
        ),
        migrations.AlterUniqueTogether(
            name='uclmanagemententity',
            unique_together=set(),
        ),
        # Make faculty nullable for reverse
        migrations.AlterField(
            model_name='uclmanagemententity',
            name='faculty',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='faculty_managements', to='base.Entity', verbose_name='faculty'),
        ),
        migrations.RunPython(forward, backward),
        migrations.AlterField(
            model_name='uclmanagemententity',
            name='entity',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='uclmanagement_entity', to='base.Entity', verbose_name='entity'),
        ),
        migrations.RemoveField(
            model_name='uclmanagemententity',
            name='faculty',
        ),
    ]
