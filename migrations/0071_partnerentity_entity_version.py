# Generated by Django 2.2.13 on 2020-07-06 13:35

import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q, OuterRef, Subquery


def generate_unique_acronym(base_acronym, EntityVersion):
    existing = EntityVersion.objects.filter(
        acronym__istartswith=base_acronym
    ).values_list('acronym', flat=True)
    i = 1
    while '{}-{}'.format(base_acronym, i) in existing:
        i += 1
    return '{}-{}'.format(base_acronym, i)


def forward(apps, schema_editor):
    """
    Create PartnerEntity -> EntityVersion relation and migrate partner entity's
    Address to EntityVersionAddress
    """
    PartnerEntity = apps.get_model('partnership', 'PartnerEntity')
    EntityVersion = apps.get_model('base', 'EntityVersion')
    EntityVersionAddress = apps.get_model('base', 'EntityVersionAddress')
    Entity = apps.get_model('base', 'Entity')

    ancestors = PartnerEntity.objects.filter(parent__isnull=True).annotate(
        partner_entity_version_id=Subquery(EntityVersion.objects.filter(
            entity__organization=OuterRef('partner__organization_id'),
            parent__isnull=True,
        ).order_by('-start_date').values('entity_id')[:1])
    )
    ancestor_ids = ancestors.values_list('pk', flat=True)

    # Migrate all parents, attaching them to the partner entity
    for partner_entity in ancestors:
        organization = partner_entity.partner.organization
        entity = Entity.objects.create(
            organization_id=organization.pk,
        )
        assert partner_entity.partner_entity_version_id
        partner_entity.entity_version = EntityVersion.objects.create(
            entity=entity,
            start_date=partner_entity.created,
            title=partner_entity.name,
            acronym=generate_unique_acronym(organization.code, EntityVersion),
            parent_id=partner_entity.partner_entity_version_id,
        )
        if partner_entity.address_id and partner_entity.address.city:
            EntityVersionAddress.objects.create(
                city=partner_entity.address.city,
                street=partner_entity.address.address,
                postal_code=partner_entity.address.postal_code,
                country=partner_entity.address.country,
                is_main=True,
                entity_version=partner_entity.entity_version,
            )

    PartnerEntity.objects.bulk_update(ancestors, ['entity_version'])

    deep_hierarchy = PartnerEntity.objects.exclude(
        Q(parent_id__in=ancestor_ids) | Q(parent__isnull=True)
    )
    assert not deep_hierarchy.exists(), "Error: Deep hierarchy for {}".format(
        deep_hierarchy.values('id', 'name', 'partner')
    )

    children = PartnerEntity.objects.filter(parent__isnull=False)
    parents_mapping = dict(ancestors.values_list('pk', 'entity_version__entity_id'))

    # Migrate all children, attaching them to their parent
    for partner_entity in children:
        organization = partner_entity.partner.organization
        partner_entity.entity_version = EntityVersion.objects.create(
            entity=Entity.objects.create(
                organization_id=organization.pk,
            ),
            start_date=partner_entity.created,
            title=partner_entity.name,
            acronym=generate_unique_acronym(organization.code, EntityVersion),
            parent_id=parents_mapping[partner_entity.parent_id],
        )
        if partner_entity.address_id and partner_entity.address.city:
            EntityVersionAddress.objects.create(
                city=partner_entity.address.city,
                street=partner_entity.address.address,
                postal_code=partner_entity.address.postal_code,
                country=partner_entity.address.country,
                is_main=True,
                entity_version=partner_entity.entity_version,
            )
    PartnerEntity.objects.bulk_update(children, ['entity_version'])


def backward(apps, schema_editor):
    """
    Migrate EntityVersionAddress into PartnerEntity Address and drop relation
    to Entity
    """
    PartnerEntity = apps.get_model('partnership', 'PartnerEntity')
    Address = apps.get_model('partnership', 'Address')
    Entity = apps.get_model('base', 'Entity')
    EntityVersionAddress = apps.get_model('base', 'EntityVersionAddress')

    entities = PartnerEntity.objects.prefetch_related(
        'entity_version__entityversionaddress_set'
    ).filter(entity_version__entityversionaddress__isnull=False)

    for entity in entities:
        address = entity.entity_version.entityversionaddress_set.all()[0]
        entity.address = Address.objects.create(
            city=address.city,
            address=address.street,
            postal_code=address.postal_code,
            country=address.country,
        )

    # Delete addresses
    EntityVersionAddress.objects.filter(
        entity_version_id__in=PartnerEntity.objects.values('entity_version')
    ).delete()

    # Delete entities
    Entity.objects.filter(
        pk__in=PartnerEntity.objects.values('entity_version__entity')
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('base', '0540_prevent_empty_address'),
        ('partnership', '0070_help_texts'),
    ]

    operations = [
        migrations.AddField(
            model_name='partnerentity',
            name='entity_version',
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='base.EntityVersion',
                verbose_name='partner',
            ),
        ),
        migrations.RunPython(forward, backward),
        migrations.AlterField(
            model_name='partnerentity',
            name='entity_version',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.PROTECT,
                to='base.EntityVersion',
                verbose_name='partner',
            ),
        ),
        migrations.RemoveField(
            model_name='partnerentity',
            name='address',
        ),
        migrations.RemoveField(
            model_name='partnerentity',
            name='parent',
        ),
        migrations.RemoveField(
            model_name='partnerentity',
            name='partner',
        ),
    ]
