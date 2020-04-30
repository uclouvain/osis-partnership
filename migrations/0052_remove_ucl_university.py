# Generated by Django 2.2.10 on 2020-04-09 09:47
import django
from django.db import migrations, models
from django.db.models import F, Subquery, OuterRef

from base.models.enums.entity_type import FACULTY


def forward(apps, schema_editor):
    Partnership = apps.get_model('partnership', 'Partnership')

    # Move ucl_university field to ucl_entity when ucl_entity (which was
    # ucl_university_labo) is null
    Partnership.objects.filter(
        ucl_entity__isnull=True,
    ).update(
        ucl_entity=F('ucl_university')
    )


def backward(apps, schema_editor):
    Partnership = apps.get_model('partnership', 'Partnership')
    EntityVersion = apps.get_model('base', 'EntityVersion')

    cte = EntityVersion.objects.with_children()
    # Get faculty of ucl_entity when ucl_entity is a not faculty
    Partnership.objects.annotate(
        entity_type=Subquery(EntityVersion.objects
            .filter(entity_id=OuterRef('ucl_entity_id'))
            .order_by('-start_date')
            .values('entity_type')[:1]),
        replacing_faculty_id=Subquery(
            cte.join(EntityVersion, id=cte.col.id).with_cte(cte).annotate(
                children=cte.col.children,
            ).filter(
                entity_type='FACULTY',
                children__contains_any=OuterRef('ucl_entity_id'),
            ).values('entity_id').distinct()[:1]
        )
    ).exclude(
        entity_type=FACULTY,
    ).update(
        ucl_university_id=F('replacing_faculty_id'),
    )

    # Move ucl_entity to ucl_university field when ucl_entity is a faculty
    Partnership.objects.annotate(
        entity_type=Subquery(EntityVersion.objects
            .filter(entity=OuterRef('ucl_entity_id'))
            .order_by('-start_date')
            .values('entity_type')[:1]),
    ).filter(
        entity_type=FACULTY,
    ).update(
        ucl_university=F('ucl_entity'),
        ucl_entity=None,
    )


class Migration(migrations.Migration):
    dependencies = [
        ('partnership', '0051_remove_faculty'),
    ]

    operations = [
        migrations.RenameField(
            model_name='partnership',
            old_name='ucl_university_labo',
            new_name='ucl_entity',
        ),
        # Make ucl_university nullable for reverse
        migrations.AlterField(
            model_name='partnership',
            name='ucl_university',
            field=models.ForeignKey(limit_choices_to=models.Q(models.Q(entityversion__entity_type='FACULTY'), models.Q(('uclmanagement_entity__isnull', False), ('parent_of__entity__uclmanagement_entity__isnull', False), _connector='OR')), null=True, on_delete=django.db.models.deletion.PROTECT, related_name='partnerships', to='base.Entity', verbose_name='ucl_university'),
        ),
        migrations.RunPython(forward, backward),
        migrations.AlterField(
            model_name='partnership',
            name='ucl_entity',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='partnerships', to='base.Entity', verbose_name='ucl_entity'),
        ),
        migrations.RemoveField(
            model_name='partnership',
            name='ucl_university',
        ),
    ]
