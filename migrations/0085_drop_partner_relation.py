import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Subquery, OuterRef, F


def forward(apps, schema_editor):
    Partnership = apps.get_model('partnership', 'Partnership')
    EntityVersion = apps.get_model('base', 'EntityVersion')

    # All partner entities must have an organization
    assert not Partnership.objects.filter(
        partner_entity__organization__isnull=True,
    ).exclude(partner_entity__isnull=True)

    # Update with the root entity version
    Partnership.objects.filter(partner_entity__isnull=True).annotate(
        partner_entity_entity=Subquery(EntityVersion.objects.filter(
            entity__organization__partner=OuterRef('partner'),
            parent__isnull=True,
        ).order_by('-start_date').values('entity_id')[:1])
    ).update(partner_entity_id=F('partner_entity_entity'))


def backwards(apps, schema_editor):
    Partnership = apps.get_model('partnership', 'Partnership')
    EntityVersion = apps.get_model('base', 'EntityVersion')
    Organization = apps.get_model('base', 'Organization')

    # Update all entities that are partners
    Partnership.objects.annotate(
        linked_to=Subquery(EntityVersion.objects.filter(
            entity=OuterRef('partner_entity'),
        ).order_by('-start_date').values('parent')[:1]),
        partner_ref=Subquery(EntityVersion.objects.filter(
            entity=OuterRef('partner_entity'),
        ).order_by('-start_date').values('entity__organization__partner')[:1])
    ).filter(
        linked_to__isnull=True,
    ).update(
        partner_id=F('partner_ref'),
        partner_entity_id=None,
    )

    # Update sub-entities
    Partnership.objects.annotate(
        partner_ref=Subquery(Organization.objects.filter(
            entity=OuterRef('partner_entity'),
            partner__isnull=False,
        ).order_by('pk').values('partner')[:1])
    ).filter(
        partner__isnull=True,
    ).update(
        partner_id=F('partner_ref'),
    )


class Migration(migrations.Migration):
    dependencies = [
        ('partnership', '0084_acronyms'),
    ]

    operations = [
        migrations.AlterField(
            model_name='partnership',
            name='partner',
            field=models.ForeignKey(
                'partnership.Partner',
                verbose_name='partner',
                on_delete=models.PROTECT,
                related_name='partnerships',
                null=True,
            ),
        ),
        migrations.RunPython(forward, backwards, elidable=True),
        migrations.AlterField(
            model_name='partnership',
            name='partner_entity',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='partner_of',
                to='base.Entity',
                verbose_name='partner_entity',
            ),
        ),
        migrations.RemoveField(
            model_name='partnership',
            name='partner',
        ),
    ]
