import datetime

from base.models.enums.entity_type import FACULTY
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_manager import EntityManagerFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.user import UserFactory
from django.test import TestCase
from django.urls import reverse
from partnership.tests.factories import (PartnerEntityFactory, PartnerFactory,
                                         PartnershipFactory,
                                         PartnershipYearFactory, PartnershipYearEducationFieldFactory,
                                         PartnershipYearEducationLevelFactory)


class PartnershipUpdateViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PersonEntityFactory(entity=entity_version.entity, person__user=cls.user_adri)
        cls.user_gf = UserFactory()
        entity_manager = EntityManagerFactory(person__user=cls.user_gf)
        cls.user_other_gf = UserFactory()
        EntityManagerFactory(person__user=cls.user_other_gf, entity=entity_manager.entity)

        # Dates :
        cls.partner = PartnerFactory()
        cls.partner_entity = PartnerEntityFactory(partner=cls.partner)

        cls.partner_gf = PartnerFactory(author=cls.user_gf)
        cls.partnership = PartnershipFactory(
            partner=cls.partner,
            partner_entity=cls.partner_entity,
            author=cls.user_gf,
            years=[],
        )
        cls.url = reverse('partnerships:update',
                          kwargs={'pk': cls.partnership.pk})

        # Years
        cls.academic_year_2149 = AcademicYearFactory(year=2149)
        cls.start_academic_year = AcademicYearFactory(year=2150)
        cls.from_academic_year = AcademicYearFactory(year=2151)
        cls.end_academic_year = AcademicYearFactory(year=2152)
        cls.academic_year_2153 = AcademicYearFactory(year=2153)

        cls.education_field = PartnershipYearEducationFieldFactory()
        cls.education_level = PartnershipYearEducationLevelFactory()

        cls.partnership.years = [
            PartnershipYearFactory(academic_year=cls.start_academic_year),
            PartnershipYearFactory(academic_year=cls.from_academic_year),
            PartnershipYearFactory(academic_year=cls.end_academic_year),
        ]

        # Ucl
        cls.ucl_university = EntityFactory()
        EntityVersionFactory(entity=cls.ucl_university, entity_type=FACULTY)
        cls.ucl_university_labo = EntityFactory()
        EntityVersionFactory(entity=cls.ucl_university_labo, parent=cls.ucl_university)
        cls.university_offer = EducationGroupYearFactory(administration_entity=cls.ucl_university_labo)

        cls.data = {
            'comment': '',
            'partner': cls.partner.pk,
            'partner_entity': cls.partner_entity.pk,
            'supervisor': '',
            'ucl_university': cls.ucl_university.pk,
            'ucl_university_labo': cls.ucl_university_labo.pk,
            'university_offers': [cls.university_offer.pk],
            'year-is_sms': True,
            'year-is_smp': False,
            'year-is_sta': True,
            'year-is_stt': False,
            'year-education_fields': [cls.education_field.pk],
            'year-education_levels': [cls.education_level.pk],
            'year-entities': [],
            'year-offers': [],
            'year-start_academic_year': cls.start_academic_year.pk,
            'year-from_academic_year': cls.from_academic_year.pk,
            'year-end_academic_year': cls.end_academic_year.pk,
        }

    def test_get_partnership_as_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partnership_update.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_partnership_as_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partnership_update.html')

    def test_get_own_partnership_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/partnership_update.html')

    def test_get_own_partnership_as_gf(self):
        self.client.force_login(self.user_gf)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership_update.html')
        self.assertNotIn('start_academic_year', response.context_data['form_year'].fields)

    def test_get_other_partnership_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/partnership_update.html')

    def test_post(self):
        self.client.force_login(self.user_adri)
        data = self.data
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership_detail.html')

    def test_post_empty(self):
        self.client.force_login(self.user_adri)
        response = self.client.post(self.url, data={}, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partnership_detail.html')
        self.assertTemplateUsed(response, 'partnerships/partnership_update.html')

    def test_post_empty_sm(self):
        self.client.force_login(self.user_adri)
        data = self.data.copy()
        data['year-is_sms'] = False
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership_detail.html')
        year = response.context_data['partnership'].years.last()
        self.assertFalse(year.education_levels.exists())
        self.assertFalse(year.entities.exists())
        self.assertFalse(year.offers.exists())

    def test_post_start_date_as_gf(self):
        self.client.force_login(self.user_gf)
        data = self.data.copy()
        data['year-start_academic_year'] = str(self.academic_year_2149.pk)
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership_detail.html')
        self.assertEqual(response.context_data['partnership'].years.count(), 3)

    def test_post_past_from_date_as_gf(self):
        self.client.force_login(self.user_gf)
        data = self.data.copy()
        data['year-from_academic_year'] = str(self.academic_year_2149.pk)
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partnership_detail.html')
        self.assertTemplateUsed(response, 'partnerships/partnership_update.html')

    def test_post_past_start_date(self):
        self.client.force_login(self.user_adri)
        data = self.data.copy()
        data['year-start_academic_year'] = str(self.academic_year_2149.pk)
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership_detail.html')
        self.assertEqual(response.context_data['partnership'].years.count(), 4)

    def test_post_post_start_date(self):
        self.client.force_login(self.user_adri)
        data = self.data.copy()
        data['year-start_academic_year'] = str(self.from_academic_year.pk)
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership_detail.html')
        self.assertEqual(response.context_data['partnership'].years.count(), 2)

    def test_post_past_from_date(self):
        self.client.force_login(self.user_adri)
        data = self.data.copy()
        data['year-from_academic_year'] = str(self.start_academic_year.pk)
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership_detail.html')
        self.assertEqual(response.context_data['partnership'].years.count(), 3)
        self.assertTrue(response.context_data['partnership'].years.first().is_sms)

    def test_post_post_from_date(self):
        self.client.force_login(self.user_adri)
        data = self.data.copy()
        data['year-from_academic_year'] = str(self.end_academic_year.pk)
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership_detail.html')
        self.assertEqual(response.context_data['partnership'].years.count(), 3)
        self.assertFalse(response.context_data['partnership'].years.first().is_sms)
        self.assertFalse(response.context_data['partnership'].years.all()[1].is_sms)
        self.assertTrue(response.context_data['partnership'].years.last().is_sms)

    def test_post_past_end_date(self):
        self.client.force_login(self.user_adri)
        data = self.data.copy()
        data['year-end_academic_year'] = str(self.academic_year_2153.pk)
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership_detail.html')
        self.assertEqual(response.context_data['partnership'].years.count(), 4)

    def test_post_post_end_date(self):
        self.client.force_login(self.user_adri)
        data = self.data.copy()
        data['year-end_academic_year'] = str(self.from_academic_year.pk)
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership_detail.html')
        self.assertEqual(response.context_data['partnership'].years.count(), 2)
