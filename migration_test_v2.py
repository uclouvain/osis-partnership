from django.conf import settings
from django.db import migrations
from partnership.models.enums.partnership import PartnershipProductionSupplement, PartnershipType, PartnershipFlowDirection, \
    PartnershipDiplomaWithUCL
from django.db.models import Min, Max


# fields: changed, education_group_year, organization,
# enrollment_place,
# done :  is_producing_cerfificate, is_producing_annexe, all_students,  diploma

# base_entity, base_organization,
# lien depuis partnership_partnership avec les base_entity
# partnership_partnership avec un id de partenaire référent si c'est le cas. (partner_referent_id)
# années gérée dans partnership_partnership_year_offer (lien vers base year offer) (lié depuis partnership_partnership -> partnership_partnership_year -> ...offer)


def migrate_data_codiplomation(apps, schema_editor):
    if settings.TESTING:
        return
    AcademicYear = apps.get_model('base', 'AcademicYear')
    EducationGroupYear = apps.get_model("base", "EducationGroupYear")
    EducationGroupOrganization = apps.get_model("base", "EducationGroupOrganization")
    Entity = apps.get_model("base", "Entity")
    Partnership = apps.get_model("partnership", "Partnership")
    PartnershipPartnerRelation = apps.get_model("partnership", "PartnershipPartnerRelation")
    PartnershipPartnerRelationYear = apps.get_model("partnership", "PartnershipPartnerRelationYear")
    PartnershipYear = apps.get_model("partnership", "PartnershipYear")
    PartnershipMission = apps.get_model("partnership", "PartnershipMission")
    PartnershipSubtype = apps.get_model("partnership", "PartnershipSubtype")
    PartnershipYearEducationLevel = apps.get_model("partnership", "PartnershipYearEducationLevel")
    PartnershipYearOffers = apps.get_model("partnership", "PartnershipYearOffers")

    all_education_group_organization = EducationGroupOrganization.objects.all().prefetch_related(
        'education_group_year__education_group').order_by(
        'education_group_year__education_group').values_list('education_group_year__education_group', flat=True)

    all_ego_set = set(all_education_group_organization)

    for item_ego in all_ego_set:
        codiplomations_by_eg = EducationGroupOrganization.objects.all().prefetch_related(
            'education_group_year__education_group').order_by(
            'education_group_year__education_group').filter(education_group_year__education_group=item_ego)

        start = codiplomations_by_eg.aggregate(min_acad=Min('education_group_year__academic_year__year'))
        end = codiplomations_by_eg.aggregate(max_acad=Max('education_group_year__academic_year__year'))

        start_date = AcademicYear.objects.get(year=start['min_acad']).start_date
        end_date = AcademicYear.objects.get(year=end['max_acad']).end_date

        newer_partnership = codiplomations_by_eg.order_by('-education_group_year__academic_year').first() # tri descend

        # Creation one partnership
        mission = PartnershipMission.objects.get(code="ENS")
        subtype = PartnershipSubtype.objects.get(code="ORG_WITH") # co-organisation avec co-diplomation

        partnership = Partnership(
            comment='',
            ucl_entity_id=newer_partnership.education_group_year.management_entity_id,  # adminstration_entity_id > management_entity_id ? pas null
            supervisor_id=None,
            author_id=None,
            partnership_type=PartnershipType.COURSE.name,
            end_date=end_date,
            start_date=start_date,
            is_public=True,
            # missions=mission,
            description='',
            subtype=subtype
        )
        partnership.save()
        partnership.missions.add(mission)

        # lien avec les entity. (entity_id qui fait le lien avec base_entity)
        # non_concerne serait les non-référents

        entities_coorganization=codiplomations_by_eg.values_list('organization', flat=True).distinct()
        for organization in entities_coorganization:
            entity_obj = Entity.objects.filter(organization_id=organization).first()
            relation = PartnershipPartnerRelation(
                    partnership=partnership,
                    entity=entity_obj
                )
            relation.save()

            referents = []
            for codiplomation_year in codiplomations_by_eg.filter(organization=organization):
                supplement = PartnershipProductionSupplement.YES.name if codiplomation_year.is_producing_annexe else PartnershipProductionSupplement.NO.name
                type_diploma = PartnershipDiplomaWithUCL.UNIQUE.name if codiplomation_year.diploma == "UNIQUE" else PartnershipDiplomaWithUCL.SEPARED.name
                referents.append(codiplomation_year.enrollment_place)
                relation_year = PartnershipPartnerRelationYear(
                    partnership_relation=relation,
                    academic_year=codiplomation_year.education_group_year.academic_year,
                    type_diploma_by_partner=type_diploma,
                    diploma_prod_by_partner=codiplomation_year.is_producing_cerfificate,
                    supplement_prod_by_partner=supplement,
                    partner_referent=codiplomation_year.enrollment_place
                )
                relation_year.save()

        # education_group_year > annuel / domain >> 23 relation
        ucl_referent = False if True in referents else False # si aucun partneraire n'est référent uclouvain est référent
        for i in range(start['min_acad'], end['max_acad']+1):
            partnership_year = PartnershipYear(
                academic_year=AcademicYear.objects.get(year=i), #codiplomation_year.education_group_year.academic_year, #educationgrouyear_academic_year
                partnership=partnership,
                funding_type=None,
                funding_program=None,
                funding_source=None,
                flow_direction=PartnershipFlowDirection.IN.name,
                ucl_reference=ucl_referent,
                all_student=codiplomation_year.all_students, # organization (
                diploma_prod_by_ucl=codiplomation_year.is_producing_cerfificate,
                supplement_prod_by_ucl=codiplomation_year.is_producing_annexe,
                type_diploma_by_ucl=PartnershipDiplomaWithUCL.UNIQUE.name
            )
            partnership_year.save()
            # isced = codiplomation.education_group_year.isced_domain if codiplomation.education_group_year.isced_domain else: ...

            type_ba = PartnershipYearEducationLevel.objects.get(code='ISCED-6')
            type_master = PartnershipYearEducationLevel.objects.get(code='ISCED-7')
            type_doct = PartnershipYearEducationLevel.objects.get(code='ISCED-8')

            dict_training = {1: type_ba,
                             2: type_master,
                             3: type_doct,
                             }

            partnership_year.education_fields.add(codiplomation_year.education_group_year.isced_domain) # reference_DomainIsced  <- base.EducationGroupYear:isced_domain_id
            partnership_year.education_levels.add(dict_training.get(codiplomation_year.education_group_year.education_group_type.cycle))
            partnership_year.entities.add(newer_partnership.education_group_year.management_entity_id) # base.EducationGroupYear
            partnership_year.offers.add() #



class Migration(migrations.Migration):
    dependencies = [
        ('partnership', '0096_auto_20250527_1438'), #0008_auto_20240723_0947
    ]

    operations = [
        migrations.RunPython(code=migrate_data_codiplomation),
    ]
