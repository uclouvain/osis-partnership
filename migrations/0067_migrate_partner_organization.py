# Generated by Django 2.2.10 on 2020-06-10 15:27
from datetime import datetime

from django.db import migrations
from django.db.models import OuterRef, Subquery, Value
from django.db.models.functions import Concat

from base.models.enums.organization_type import *


def forward(apps, schema_editor):
    Partner = apps.get_model('partnership', 'Partner')
    Organization = apps.get_model('base', 'Organization')
    EntityVersion = apps.get_model('base', 'EntityVersion')
    Entity = apps.get_model('base', 'Entity')

    # Fill the organization_id with matching external_id
    Partner.objects.update(
        organization_id=Subquery(Organization.objects.filter(
            external_id=Concat(
                Value('osis.organization_'),
                OuterRef('external_id'),
            ),
        ).values('pk').order_by('pk'))
    )

    Entity.objects.filter(organization__partner__isnull=False).update(
        website=Subquery(Organization.objects.filter(
            pk=OuterRef('organization'),
        ).values('partner__website').order_by('pk')[:1])
    )

    unmatched = Partner.objects.filter(organization__isnull=True)

    type_mapping = {
        1: EMBASSY,
        2: OTHER,
        3: RESEARCH_CENTER,
        4: ENTERPRISE,
        5: HOSPITAL,
        6: NGO,
        7: ACADEMIC_PARTNER,
    }
    # Si aucun résultat:  Création d'une nouvelle organisation et ajout de l'ID
    # dans la relation One-To-One du partner
    for partner in unmatched:
        partner.organization_id = Organization.objects.create(
            name=partner.name,
            code=partner.partner_code or '',
            type=type_mapping[partner.partner_type_id],
            external_id='osis.organization_' + partner.external_id
            if partner.external_id else '',
        ).pk
        # also create the corresponding Entity and EntityVersion
        entity = Entity.objects.create(
            organization_id=partner.organization_id,
            website=partner.website,
        )
        EntityVersion.objects.create(
            entity_id=entity.pk,
            start_date=partner.start_date or partner.created,
            end_date=partner.end_date,
            title=partner.name,
        )
    Partner.objects.bulk_update(unmatched, ['organization_id'])

    unmatched = Partner.objects.filter(organization__isnull=True)
    assert not unmatched.exists(), '{} unmatched'.format(unmatched.count())


def backward(apps, schema_editor):
    Partner = apps.get_model('partnership', 'Partner')
    Organization = apps.get_model('base', 'Organization')
    EntityVersion = apps.get_model('base', 'EntityVersion')
    PartnerType = apps.get_model('partnership', 'PartnerType')

    # Create the partner types
    type_mapping = {
        EMBASSY: PartnerType.objects.create(value=EMBASSY),
        OTHER: PartnerType.objects.create(value=OTHER),
        RESEARCH_CENTER: PartnerType.objects.create(value=RESEARCH_CENTER),
        ENTERPRISE: PartnerType.objects.create(value=ENTERPRISE),
        HOSPITAL: PartnerType.objects.create(value=HOSPITAL),
        NGO: PartnerType.objects.create(value=NGO),
        ACADEMIC_PARTNER: PartnerType.objects.create(value=ACADEMIC_PARTNER),
    }

    # Fill the fields with organization values
    now = datetime.now()
    Partner.objects.annotate(
        organization_type=Subquery(Organization.objects.filter(
            pk=OuterRef('organization_id'),
        ).values('type').order_by('pk')),
    ).update(
        partner_type=Subquery(PartnerType.objects.filter(
            value=OuterRef('organization_type'),
        ).values('pk')),
        external_id=Subquery(Organization.objects.filter(
            pk=OuterRef('organization_id'),
        ).exclude(
            external_id='',
        ).values('external_id').order_by('pk')),
        name=Subquery(Organization.objects.filter(
            pk=OuterRef('organization_id'),
        ).values('name').order_by('pk')),
        partner_code=Subquery(Organization.objects.filter(
            pk=OuterRef('organization_id'),
        ).exclude(
            code='',
        ).values('code').order_by('pk')),
        start_date=Subquery(EntityVersion.objects.filter(
            entity__organization=OuterRef('organization_id'),
            parent__isnull=True,
        ).order_by('start_date').values('start_date')[:1]),
        end_date=Subquery(EntityVersion.objects.filter(
            entity__organization=OuterRef('organization_id'),
            parent__isnull=True,
        ).order_by('-start_date').values('end_date')[:1]),
        website=Subquery(EntityVersion.objects.current(now).filter(
            entity__organization=OuterRef('organization_id'),
            parent__isnull=True,
        ).order_by('-start_date').values('entity__website')[:1]),
    )

    # Change the partner types for human-readable values
    readable_values = dict(ORGANIZATION_TYPE)
    for name, partner_type in type_mapping.items():
        partner_type.value = readable_values[name]
        partner_type.save()


class Migration(migrations.Migration):
    dependencies = [
        ('partnership', '0066_add_partner_organization'),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
