from django.conf import settings
from django.db import migrations


def migrate_data_codiplomation(apps):
    if settings.TESTING:
        return
    EducationGroupYear = apps.get_model("base", "EducationGroupYear")
    EducationGroupOrganization = apps.get_model("base", "EducationGroupOrganization")
    Partnership = apps.get_model("Partnership", "Partnership")
    Relation = apps.get_model("Partnership", "Relation")
    PartnershipYear = apps.get_model("Patnership", "PartnershipYear")
    PartnershipMission = apps.get_model("Partnership", "PartnershipMission")


    all_education_group_organization = EducationGroupOrganization.objects.all()

    for codiplomation in all_education_group_organization:
        # fields: changed, education_group_year, organization,
        # enrollment_place,
        #done :  is_producing_cerfificate, is_producing_annexe, all_students,  diploma

        #loop for annualization
        #base_entity, base_organization,
        #lien depuis partnership_partnership avec les base_entity
        # partnership_partnership avec un id de partenaire référent si c'est le cas. (partner_referent_id)
        # années gérée dans partnership_partnership_year_offer (lien vers base year offer) (lié depuis partnership_partnership -> partnership_partnership_year -> ...offer)

        mission = PartnershipMission.objects.get(code="ENS")

        # a + b = z 2022
        # a + b = zbis 2023

        # prepare object
        partnership_codiplomation = Partnership(
            comment= None,
            ucl_entity_id = ...,
            supervisor_id = ...,
            author_id=...,
            partnership_type = "COURSE",
            end_date="",
            start_date="",
            is_public=True,
            description=None,
            subtype_id = ...,
            missions =  [mission],
            ucl_reference = True,
            partner_referent = None,
            all_student = codiplomation.all_students,
            diploma_by_ucl = codiplomation.diploma,
            diploma_prod_by_ucl = codiplomation.is_producing_cerfificate,
            supplement_prod_by_ucl = codiplomation.is_producing_annexe,
            # other fields

        )

        #lien avec les entity. (entity_id qui fait le lien avec base_entity)
        #non_concerne serait les non-référents
        relation = Relation(
            partnership=partnership_codiplomation,
            entity= ...,
            diploma_with_ucl_by_partner = ...,
            diploma_prod_by_partner= not codiplomation.is_producing_cerfificate,
            supplement_prod_by_partner = not codiplomation.is_producing_annexe,
        )
        # education_group_year > anuuel / domain >> 23 relation
        PartnershipYear(
            academic_year_id=...,
            partnership_id=...,
            is_smp=False,
            is_sms=False,
            is_sta=False,
            is_stt=False,
            eligible=False,
            is_smt=False,
            funding_type_id=None,
            funding_program_id = None,
            funding_source_id = None,
            education_fields_id = codiplomation.education_group_year, #reference.DomainIsced  -> base.EducationGroupYear:isced_domain_id
            education_levels_id = ..., # partnership.PartnershipYearEducationLevel
            entities = ..., #partnership_year_entities > Base-entity
            offers = ..., # base.EducationGroupYear
        )
        # questions :
        # - pas le lien avec l'entité qui conclu le partenariat (dans ucl), ok de faire le lien avec la fac
        #  qui organise la formation directement ?
        # - pas d'historique si changement de qui imprime le diplôme dans un même partenariat

        # save object
        partnership_codiplomation.save()
        relation.save()

        # delete old object
        codiplomation.delete()


class Migration(migrations.Migration):
    dependencies = [
        ('partnership', '0008_auto_20240723_0947'),
    ]

    operations = [
        migrations.RunPython(migrate_data_codiplomation, ),
    ]
