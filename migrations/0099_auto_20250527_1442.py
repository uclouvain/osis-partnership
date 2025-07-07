from django.conf import settings
from django.db import migrations, models
from django.db.models import Min

from partnership.models.enums.partnership import PartnershipProductionSupplement, PartnershipType, \
    PartnershipFlowDirection, \
    PartnershipDiplomaWithUCL


def migrate_data_codiplomation(apps, schema_editor):
    """
        Migration to import historical data from base_organization into the partnerhsip module
    """
    if settings.TESTING:
        return
    AcademicYear = apps.get_model('base', 'AcademicYear')
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
        'education_group_year__education_group'
    ).order_by(
        'education_group_year__education_group'
    ).values_list('education_group_year__education_group', flat=True)

    all_ego_set = set(all_education_group_organization)

    for item_ego in all_ego_set:
        codiplomations_by_eg = EducationGroupOrganization.objects.all().prefetch_related(
            'education_group_year__education_group'
        ).order_by(
            'education_group_year__education_group'
        ).filter(education_group_year__education_group=item_ego)

        test_date_fin = codiplomations_by_eg.first().education_group_year.education_group.end_year
        if test_date_fin:
            end_date = test_date_fin.end_date
            end = {'max_acad': test_date_fin.year}
        else:
            end = {'max_acad': 2037}
            end_date = AcademicYear.objects.get(year=end['max_acad']).end_date

        start = codiplomations_by_eg.aggregate(min_acad=Min('education_group_year__academic_year__year'))
        start_date = AcademicYear.objects.get(year=start['min_acad']).start_date

        newer_partnership = codiplomations_by_eg.order_by('-education_group_year__academic_year').first()  # tri descend

        # Creation one partnership
        mission = PartnershipMission.objects.get(code="ENS")
        subtype = PartnershipSubtype.objects.get(code="ORG_WITH")  # label : co-organisation avec co-diplomation

        partnership = Partnership(
            comment='',
            ucl_entity_id=newer_partnership.education_group_year.management_entity_id,
            supervisor_id=None,
            author_id=None,
            partnership_type=PartnershipType.COURSE.name,
            end_date=end_date,
            start_date=start_date,
            is_public=True,
            description='',
            subtype=subtype
        )
        partnership.save()
        partnership.missions.add(mission)

        # id of entity partner to create the partner relationship
        referents = {}
        all_id_entities_coorganization = codiplomations_by_eg.values_list('organization', flat=True).distinct()
        for partner_id in all_id_entities_coorganization:
            entity_obj = Entity.objects.filter(organization_id=partner_id).first()
            relation = PartnershipPartnerRelation(
                partnership=partnership,
                entity=entity_obj
            )
            relation.save()

            # Creation of the relationship year
            partner_years = codiplomations_by_eg.filter(organization=partner_id).order_by(
                'education_group_year__academic_year')
            for partner_year in partner_years:
                supplement = PartnershipProductionSupplement.YES.name if partner_year.is_producing_annexe else PartnershipProductionSupplement.NO.name
                type_diploma = PartnershipDiplomaWithUCL.UNIQUE.name if partner_year.diploma == PartnershipDiplomaWithUCL.UNIQUE.name else PartnershipDiplomaWithUCL.NO_CODIPLOMA.name
                year = partner_year.education_group_year.academic_year.year
                if not referents.get(year):
                    referents[year] = [partner_year.enrollment_place]
                else:
                    referents[year].append(partner_year.enrollment_place)

                relation_year = PartnershipPartnerRelationYear(
                    partnership_relation=relation,
                    academic_year=partner_year.education_group_year.academic_year,
                    type_diploma_by_partner=type_diploma,
                    diploma_prod_by_partner=partner_year.is_producing_cerfificate,
                    supplement_prod_by_partner=supplement,
                    partner_referent=partner_year.enrollment_place,
                    all_student=partner_year.all_students
                )
                relation_year.save()

        for i in range(start['min_acad'], end['max_acad'] + 1):
            value_referent_year = referents.get(i)
            if value_referent_year:
                ucl_referent = False if True in value_referent_year else True  # if no partner is referent uclouvain is referent
            else:
                ucl_referent = True

            partnership_year = PartnershipYear(
                academic_year=AcademicYear.objects.get(year=i),
                partnership=partnership,
                funding_type=None,
                funding_program=None,
                funding_source=None,
                flow_direction=PartnershipFlowDirection.IN.name,
                ucl_reference=ucl_referent,
                all_student=True,
                diploma_prod_by_ucl=partner_year.is_producing_cerfificate,
                supplement_prod_by_ucl=PartnershipProductionSupplement.YES.name if partner_year.is_producing_annexe else PartnershipProductionSupplement.NO.name,
                type_diploma_by_ucl=PartnershipDiplomaWithUCL.UNIQUE.name
            )
            partnership_year.save()

            type_ba = PartnershipYearEducationLevel.objects.get(code='ISCED-6')
            type_master = PartnershipYearEducationLevel.objects.get(code='ISCED-7')
            type_doct = PartnershipYearEducationLevel.objects.get(code='ISCED-8')

            dict_training = {
                1: type_ba,
                2: type_master,
                3: type_doct,
            }

            partnership_year.education_fields.add(
                partner_year.education_group_year.isced_domain
            )  # reference_DomainIsced  <- base.EducationGroupYear:isced_domain_id
            partnership_year.education_levels.add(
                dict_training.get(partner_year.education_group_year.education_group_type.cycle)
            )
            partnership_year.entities.add(newer_partnership.education_group_year.management_entity_id)
            offer = PartnershipYearOffers(
                partnershipyear=partnership_year,
                educationgroup=partner_year.education_group_year.education_group,
                educationgroupyear=partner_year.education_group_year,
                external_id=f"osis.partnership_year_offers_{partner_year.external_id.split('_')[-1]}",
            )
            offer.save()


class Migration(migrations.Migration):
    dependencies = [
        ('partnership', '0098_auto_20250527_1438'),
    ]

    operations = [
        migrations.AddField(
            model_name='partnershipyearoffers',
            name='external_id',
            field=models.CharField(blank=True, max_length=100, null=True, editable=False),
        ),
        migrations.RunPython(code=migrate_data_codiplomation),
    ]
