from datetime import date, timedelta

from django.shortcuts import resolve_url
from django.test import TestCase
from django.urls import reverse

from base.models.enums.entity_type import FACULTY, SECTOR
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.user import UserFactory
from partnership.models import PartnershipType
from partnership.tests.factories import (
    FundingTypeFactory, PartnerEntityFactory,
    PartnerFactory,
    PartnershipEntityManagerFactory,
    PartnershipFactory, PartnershipYearEducationLevelFactory,
    PartnershipYearFactory, UCLManagementEntityFactory,
)
from partnership.tests.factories.partnership_year import (
    PartnershipMissionFactory,
)
from reference.tests.factories.domain_isced import DomainIscedFactory


class PartnershipCreateProjectViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(
            entity=entity_version.entity,
            person__user=cls.user,
            scopes=[PartnershipType.PROJECT.name]
        )

        cls.partner = PartnerFactory()
        cls.partner_entity = PartnerEntityFactory(partner=cls.partner)

        AcademicYearFactory.produce_in_future(date.today().year, 3)

        cls.education_field = DomainIscedFactory()
        cls.education_level = PartnershipYearEducationLevelFactory()

        cls.url = reverse(
            'partnerships:create',
            kwargs={'type': PartnershipType.PROJECT},
        )

        # Ucl
        root = EntityVersionFactory(parent=None).entity
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
            'partnership_type': PartnershipType.PROJECT.name,
            'comment': '',
            'partner': cls.partner.pk,
            'partner_entity': cls.partner_entity.pk,
            'supervisor': PersonFactory().pk,
            'ucl_entity': cls.ucl_university.pk,
            'university_offers': [cls.university_offer.pk],
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=365),
            'year-education_fields': [cls.education_field.pk],
            'year-education_levels': [cls.education_level.pk],
            'year-missions': PartnershipMissionFactory().pk,
            'year-funding': 'fundingtype-%s' % FundingTypeFactory().pk,
            'year-project_title': "Project title 1",
            'year-id_number': "#132456",
            'year-ucl_status': "coordinator",
        }
        PartnershipMissionFactory()

    def test_get_view_as_adri(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_create.html')

    def test_post(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, data=self.data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_detail.html')


class PartnershipUpdateProjectViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(
            entity=entity_version.entity,
            person__user=cls.user,
            scopes=[PartnershipType.PROJECT.name]
        )

        # Dates :
        cls.partner = PartnerFactory()
        cls.partner_entity = PartnerEntityFactory(partner=cls.partner)

        # Years
        cls.start_academic_year = AcademicYearFactory(year=2150)
        cls.from_academic_year = AcademicYearFactory(year=2151)
        cls.end_academic_year = AcademicYearFactory(year=2152)

        cls.education_field = DomainIscedFactory()
        cls.education_level = PartnershipYearEducationLevelFactory()

        # Ucl
        root = EntityVersionFactory(parent=None).entity
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
            partnership_type=PartnershipType.PROJECT.name,
            partner=cls.partner,
            partner_entity=cls.partner_entity,
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
        cls.url = resolve_url('partnerships:update', pk=cls.partnership.pk)

        cls.type = FundingTypeFactory()
        cls.data = {
            'comment': '',
            'partner': cls.partner.pk,
            'partner_entity': cls.partner_entity.pk,
            'supervisor': cls.user.person.pk,
            'ucl_entity': cls.ucl_university_labo.pk,
            'start_date': cls.from_academic_year.start_date,
            'end_date': cls.end_academic_year.end_date,
            'year-education_fields': [cls.education_field.pk],
            'year-education_levels': [cls.education_level.pk],
            'year-missions': [
                PartnershipMissionFactory().pk,
                PartnershipMissionFactory().pk,
            ],
            'year-funding': 'fundingtype-%s' % cls.type.pk,
            'year-project_title': "Project title 1",
            'year-id_number': "#132456",
            'year-ucl_status': "coordinator",
        }

    def test_get_own_partnership_as_adri(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_update.html')
        self.assertTrue(self.partnership.is_valid)

    def test_post_partnership(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, data=self.data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_detail.html')
        year = self.partnership.years.last()
        self.assertTrue(year.is_valid)
        self.assertEqual(year.funding_source_id, self.type.program.source_id)
        self.assertEqual(year.funding_program_id, self.type.program_id)
        self.assertEqual(year.funding_type_id, self.type.pk)

    def test_post_bad_funding(self):
        self.client.force_login(self.user)
        data = self.data.copy()
        data['year-funding'] = 'foobar'
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partnership/partnership_detail.html')

    def test_post_financing_program(self):
        self.client.force_login(self.user)
        data = self.data.copy()
        data['year-funding'] = 'fundingprogram-%s' % self.type.program_id
        self.client.post(self.url, data=data, follow=True)

        # Year should have changed
        year = self.partnership.years.last()
        self.assertEqual(year.funding_source_id, self.type.program.source_id)
        self.assertEqual(year.funding_program_id, self.type.program_id)
        self.assertIsNone(year.funding_type_id)

    def test_post_financing_source(self):
        self.client.force_login(self.user)
        data = self.data.copy()
        data['year-funding'] = 'fundingsource-%s' % self.type.program.source_id
        self.client.post(self.url, data=data, follow=True)

        # Year should have changed
        year = self.partnership.years.last()
        self.assertEqual(year.funding_source_id, self.type.program.source_id)
        self.assertIsNone(year.funding_program_id)
        self.assertIsNone(year.funding_type_id)

        # If we get it again, initial should be ok
        response = self.client.get(self.url)
        form = response.context_data['form_year']
        self.assertEqual(form.fields['funding'].initial, self.type.program.source)
