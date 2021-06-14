# Generated by Django 2.2.10 on 2020-04-23 15:52
import csv
from pathlib import Path

from django.conf import settings
from django.db import migrations, models
from django.db.models import Exists, F, OuterRef, Subquery


def forward(apps, schema_editor):
    PartnershipYear = apps.get_model('partnership', 'PartnershipYear')
    DomainIsced = apps.get_model('reference', 'DomainIsced')
    PartnershipYearEducationField = apps.get_model(
        'partnership', 'PartnershipYearEducationField'
    )

    # Get unmatched education fields codes
    missing_codes = PartnershipYearEducationField.objects.annotate(
        matching=Exists(DomainIsced.objects.filter(
            code=OuterRef('code')
        ))
    ).filter(matching=False).values_list('code', flat=True)

    # Load CSV into a mapping by code
    mapping = {}
    with Path(settings.BASE_DIR, 'partnership/fixtures/domains_isced.csv').open(encoding='utf8') as f:
        csv_content = csv.DictReader(f, delimiter=";")
        for row in csv_content:
            mapping[row['code']] = {**row, 'is_ares': bool(row['is_ares'])}

    new_objects = []
    for missing_code in missing_codes:
        new_objects.append(DomainIsced(**mapping[missing_code]))

    # Add new domains
    DomainIsced.objects.bulk_create(new_objects)

    old_through = PartnershipYear.education_fields.through
    new_through = PartnershipYear.new_education_fields.through

    # Annotate all relations with what their id is on DomainIsced
    qs = old_through.objects.annotate(
        domainisced_id=Subquery(DomainIsced.objects.filter(
            code=OuterRef('partnershipyeareducationfield__code')
        ).values('pk')[:1])
    ).values('domainisced_id', 'partnershipyear_id')

    # Add new relations
    new_through.objects.bulk_create(
        [new_through(**values) for values in qs]
    )


def backward(apps, schema_editor):
    PartnershipYear = apps.get_model('partnership', 'PartnershipYear')
    DomainIsced = apps.get_model('reference', 'DomainIsced')
    PartnershipYearEducationField = apps.get_model(
        'partnership', 'PartnershipYearEducationField'
    )

    old_through = PartnershipYear.new_education_fields.through
    new_through = PartnershipYear.education_fields.through

    # Create all education fields needed
    qs = DomainIsced.objects.filter(
        pk__in=Subquery(old_through.objects.values('domainisced_id'))
    ).annotate(
        label=F('title_fr')
    ).values('uuid', 'code', 'label')
    PartnershipYearEducationField.objects.bulk_create(
        [PartnershipYearEducationField(**values) for values in qs]
    )

    # Annotate all relations with what their id is on DomainIsced
    qs = old_through.objects.annotate(
        partnershipyeareducationfield_id=Subquery(
            PartnershipYearEducationField.objects.filter(
                code=OuterRef('domainisced__code')
            ).values('pk')[:1]
        )
    )

    qs = qs.values('partnershipyeareducationfield_id', 'partnershipyear_id')

    new_through.objects.bulk_create(
        [new_through(**values) for values in qs]
    )


class Migration(migrations.Migration):
    dependencies = [
        ('reference', '0004_domainisced_is_ares'),
        ('partnership', '0052_remove_ucl_university'),
    ]

    operations = [
        migrations.AddField(
            model_name='partnershipyear',
            name='new_education_fields',
            field=models.ManyToManyField(
                to='reference.DomainIsced',
                verbose_name='partnership_year_education_fields',
            ),
        ),
        migrations.RunPython(forward, backward, elidable=True),
        migrations.RemoveField(
            model_name='partnershipyear',
            name='education_fields',
        ),
        migrations.RenameField(
            model_name='partnershipyear',
            old_name='new_education_fields',
            new_name='education_fields',
        ),
        migrations.DeleteModel(
            name='PartnershipYearEducationField',
        ),
    ]
