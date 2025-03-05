from django.contrib.auth.models import Permission
from django.shortcuts import resolve_url
from django.test import TestCase
from django.urls import reverse

from base.models.enums.entity_type import FACULTY, SECTOR
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.user import UserFactory
from partnership.models import PartnershipType, PartnershipDiplomaWithUCL, PartnershipProductionSupplement
from partnership.tests.factories import (
    FundingTypeFactory, PartnerEntityFactory,
    PartnerFactory,
    PartnershipEntityManagerFactory,
    PartnershipFactory, PartnershipYearEducationLevelFactory,
    PartnershipYearFactory, UCLManagementEntityFactory,
)
from partnership.tests.factories.partnership import PartnershipConfigurationFactory
from partnership.tests.factories.partnership_year import \
    (
    PartnershipMissionFactory,
    PartnershipSubtypeFactory,
)
from reference.tests.factories.domain_isced import DomainIscedFactory


class PartnershipCreateCourseViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(is_superuser=True)
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(
            entity=entity_version.entity,
            person__user=cls.user,
            scopes=[PartnershipType.COURSE.name, PartnershipType.GENERAL.name]
        )

        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(
            entity=entity_version.entity,
            person__user=cls.user_adri,
            scopes=[PartnershipType.COURSE.name, PartnershipType.GENERAL.name]
        )
        a = Permission.objects.get(codename='change_partnership')
        cls.user.user_permissions.set([a.pk])


        cls.partner = PartnerFactory()
        cls.partner_entity = PartnerEntityFactory(partner=cls.partner)

        AcademicYearFactory.produce_in_future(quantity=3)

        cls.education_field = DomainIscedFactory()
        cls.education_level = PartnershipYearEducationLevelFactory()

        cls.url = reverse(
            'partnerships:create',
            kwargs={'type': PartnershipType.COURSE},
        )

        cls.start_academic_year = AcademicYearFactory(year=2150)
        cls.end_academic_year = AcademicYearFactory(year=2151)

        # Ucl
        root = EntityVersionFactory(parent=None, entity_type='').entity
        sector = EntityVersionFactory(entity_type=SECTOR, parent=root).entity
        cls.ucl_university = EntityVersionFactory(
            parent=sector,
            entity_type=FACULTY,
        ).entity
        cls.ucl_university_labo = EntityVersionFactory(
            parent=cls.ucl_university,
        ).entity
        UCLManagementEntityFactory(entity=cls.ucl_university)

        cls.university_offer = EducationGroupYearFactory(administration_entity=cls.ucl_university_labo)

        cls.data = {
            'partnership_type': PartnershipType.COURSE.name,
            'comment': '',
            'partner': cls.partner.pk,
            'partner_entities': [cls.partner_entity.entity_id],
            'supervisor': PersonFactory().pk,
            'ucl_entity': cls.ucl_university.pk,
            'university_offers': [cls.university_offer.pk],
            'education_fields': [cls.education_field.pk],
            'education_levels': [cls.education_level.pk],
            'entities': [],
            'offers': [],
            'start_academic_year': cls.start_academic_year.pk,
            'end_academic_year': cls.end_academic_year.pk,
            'funding_type': FundingTypeFactory().pk,
            'missions': [3, 2],
            'subtype': '',
            'all_student': True,
            'ucl_reference': True,
            'diploma_prod_by_ucl': True,
            'type_diploma_by_ucl': PartnershipDiplomaWithUCL.SEPARED.name,
            'supplement_prod_by_ucl': PartnershipProductionSupplement.SHARED.name,
        }

    def test_get_view_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_create.html')

    def test_post(self):
        self.client.force_login(self.user_adri)
        response = self.client.post(self.url, data=self.data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_create.html')


class PartnershipUpdateCourseViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(is_superuser=True)
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(
            entity=entity_version.entity,
            person__user=cls.user,
            scopes=[PartnershipType.COURSE.name]
        )

        # Dates :
        cls.partner = PartnerFactory()
        cls.partner_entity = PartnerEntityFactory(partner=cls.partner)

        # Years
        cls.academic_year_2149 = AcademicYearFactory(year=2149)
        cls.start_academic_year = AcademicYearFactory(year=2150)
        cls.from_academic_year = AcademicYearFactory(year=2151)
        cls.end_academic_year = AcademicYearFactory(year=2152)

        cls.education_field = DomainIscedFactory()
        cls.education_level = PartnershipYearEducationLevelFactory()

        # Ucl
        root = EntityVersionFactory(parent=None, entity_type='').entity
        sector = EntityVersionFactory(entity_type=SECTOR, parent=root).entity
        cls.ucl_university = EntityVersionFactory(
            parent=sector,
            entity_type=FACULTY,
        ).entity
        UCLManagementEntityFactory(entity=cls.ucl_university)
        cls.ucl_university_labo = EntityVersionFactory(
            parent=cls.ucl_university,
        ).entity
        UCLManagementEntityFactory(entity=cls.ucl_university_labo)

        cls.partnership = PartnershipFactory(
            partnership_type=PartnershipType.COURSE.name,
            partner=cls.partner,
            partner_entity=cls.partner_entity.entity,
            author=cls.user.person,
            years=[],
            ucl_entity=cls.ucl_university,
        )
        PartnershipYearFactory(
            partnership=cls.partnership,
            academic_year=cls.start_academic_year,
        )
        PartnershipYearFactory(
            partnership=cls.partnership,
            academic_year=cls.from_academic_year,
        )
        PartnershipYearFactory(
            partnership=cls.partnership,
            academic_year=cls.end_academic_year,
        )
        # Initialize config
        PartnershipConfigurationFactory(
            partnership_creation_update_min_year_id=cls.academic_year_2149.pk
        )

        root = EntityVersionFactory(parent=None, entity_type='').entity
        sector = EntityVersionFactory(entity_type='SECTOR', parent=root).entity
        cls.ucl_university = EntityVersionFactory(parent=sector, entity_type='FACULTY').entity
        cls.ucl_university_labo = EntityVersionFactory(parent=cls.ucl_university).entity
        cls.university_offer = EducationGroupYearFactory(administration_entity=cls.ucl_university_labo)

        cls.url = resolve_url('partnerships:update', pk=cls.partnership.pk)

        cls.data = {
            'partnership_type': PartnershipType.COURSE.name,
            'comment': '',
            'partner': cls.partner.pk,
            'partner_entities': [cls.partner_entity.entity_id],
            'supervisor': PersonFactory().pk,
            'ucl_entity': cls.ucl_university.pk,
            'university_offers': [cls.university_offer.pk],
            'education_fields': [cls.education_field.pk],
            'education_levels': [cls.education_level.pk],
            'entities': [],
            'offers': [],
            'start_academic_year': cls.start_academic_year.pk,
            'end_academic_year': cls.end_academic_year.pk,
            'funding_type': FundingTypeFactory().pk,
            'all_student': True,
            'ucl_reference': True,
            'diploma_prod_by_ucl': True,
            'type_diploma_by_ucl': PartnershipDiplomaWithUCL.SEPARED.name,
            'supplement_prod_by_ucl': PartnershipProductionSupplement.SHARED.name,
            'missions': [
                PartnershipMissionFactory().pk,
                PartnershipMissionFactory().pk,
            ],
            'subtype': PartnershipSubtypeFactory().pk,
        }

    def test_get_own_partnership_as_adri(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_update.html')

    def test_post_partnership(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, data=self.data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_update.html')
