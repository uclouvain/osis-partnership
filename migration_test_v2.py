from django.conf import settings
from django.db import migrations

from base.models.academic_year import AcademicYear
from models.enums.partnership import PartnershipProductionSupplement
from django.db.models import Min, Max
# fields: changed, education_group_year, organization,
# enrollment_place,
# done :  is_producing_cerfificate, is_producing_annexe, all_students,  diploma

# base_entity, base_organization,
# lien depuis partnership_partnership avec les base_entity
# partnership_partnership avec un id de partenaire référent si c'est le cas. (partner_referent_id)
# années gérée dans partnership_partnership_year_offer (lien vers base year offer) (lié depuis partnership_partnership -> partnership_partnership_year -> ...offer)


def migrate_data_codiplomation(apps):
    if settings.TESTING:
        return
    EducationGroupYear = apps.get_model("base", "EducationGroupYear")
    EducationGroupOrganization = apps.get_model("base", "EducationGroupOrganization")
    Entity = apps.get_model("Base", "Entity")
    Partnership = apps.get_model("Partnership", "Partnership")
    Relation = apps.get_model("Partnership", "Relation")
    RelationYear = apps.get_model("Partnership", "RelationYear")
    PartnershipYear = apps.get_model("Patnership", "PartnershipYear")
    PartnershipMission = apps.get_model("Partnership", "PartnershipMission")
    PartnershipYearOffers = apps.get_model("Partnership", "PartnershipYearOffers")

    all_education_group_organization = EducationGroupOrganization.objects.all().prefetch_related(
        'education_group_year__education_group').order_by(
        'education_group_year__education_group').values_list('education_group_year__education_group', flat=True)

    all_ego_set = set(all_education_group_organization)

    for item_ego in all_ego_set:
        codiplomations_by_eg = EducationGroupOrganization.objects.all().prefetch_related(
            'education_group_year__education_group').order_by(
            'education_group_year__education_group').filter(education_group_year__education_group=item_ego)

        start = codiplomations_by_eg.aggregate(min_acad=Min('education_group_year__academic_year__year'))
        end = codiplomations_by_eg.aggregate(min_acad=Max('education_group_year__academic_year__year'))

        start_date = AcademicYear.objects.get(year=start['min_acad'])
        end_date = AcademicYear.objects.get(year=end['max_acad'])

        old_partnership = codiplomations_by_eg.order_by('-academic_year').first() # tri descend

        # Creation one partnership
        mission = PartnershipMission.objects.get(code="ENS")
        # todo: find this : codiplomation.education_group_year


        partnership = Partnership(
            comment=None,
            ucl_entity_id=...,  # adminstration_entity_id > management_entity_id ? pas null
            supervisor_id=None,  #
            author_id=None,  #
            partnership_type="COURSE",
            end_date=end_date,
            start_date=start_date,
            is_public=True,
            description=None,
            subtype_id=None, # subtype ? Par défaut c'est quoi ?
            missions=[mission],
            ucl_reference=True,
            partner_referent=None,
            all_student=old_partnership.all_students,
            diploma_by_ucl=old_partnership.diploma,
            diploma_prod_by_ucl=old_partnership.is_producing_cerfificate,
            supplement_prod_by_ucl=old_partnership.is_producing_annexe,
            # other fields
        )

        # lien avec les entity. (entity_id qui fait le lien avec base_entity)
        # non_concerne serait les non-référents

        entity = Entity.objects.filter(old_partnership.organization_id)

        relation = Relation(
            partnership=partnership,
            entity= entity.first()
        )

        for codiplomation in codiplomations_by_eg:  # todo : loop for academic years
            # codiplomation format : "BBBEB100B - BBEB1BA - 2024-25 (Katholieke Universiteit Leuven)"
            supplement = PartnershipProductionSupplement.YES.name if codiplomation.is_producing_annexe else PartnershipProductionSupplement.NO.name

            relation_year = RelationYear(
                partnership_relation=relation,
                academic_year=codiplomation.academic_year,
                type_diploma_by_partner='', # PartnershipDiplomaWithUCL
                diploma_prod_by_partner=False,
                supplement_prod_by_partner=supplement,
                partner_referent=False
            )

            # education_group_year > annuel / domain >> 23 relation
            partnership_year = PartnershipYear(
                academic_year=codiplomation.academic_year,
                partnership=partnership,
                is_smp=False,
                is_sms=False,
                is_sta=False,
                is_stt=False,
                eligible=False,
                is_smt=False,
                funding_type_id=None,
                funding_program_id=None,
                funding_source_id=None,
                education_fields_id= codiplomation.isced_domain_id, # reference_DomainIsced  <- base.EducationGroupYear:isced_domain_id
                education_levels= partnership.PartnershipYearEducationLevel,
                entities=entity,  # partnership_year_entities > Base-entity ?? many-to-many? A vérifier.
                # offers=PartnershipYearOffers(),  # base.EducationGroupYear
            )
            relation_year.save()
            partnership_year.save()


        # save object
        partnership.save()

        relation.save()


class Migration(migrations.Migration):
    dependencies = [
        ('partnership', '0008_auto_20240723_0947'),
    ]

    operations = [
        migrations.RunPython(migrate_data_codiplomation, ),
    ]
