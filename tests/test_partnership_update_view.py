from django.test import TestCase
from django.urls import reverse
import datetime

from base.tests.factories.user import UserFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.entity_manager import EntityManagerFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from partnership.tests.factories import (
    PartnershipFactory, PartnerFactory,
    PartnershipYearFactory, PartnerEntityFactory)


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
        cls.date_ok = datetime.datetime.today() + datetime.timedelta(365)
        cls.date_ko = datetime.datetime.today() - datetime.timedelta(365)

        cls.partner_entity = PartnerEntityFactory()
        cls.partner = PartnerFactory()
        cls.partner_gf = PartnerFactory(author=cls.user_gf)
        cls.partnership = PartnershipFactory(partner=cls.partner,
                                             partner_entity=cls.partner_entity)
        cls.partnership_ko = PartnershipFactory(partner=cls.partner,
                                            partner_entity=cls.partner_entity,
                                            start_date=cls.date_ko)
        cls.url = reverse('partnerships:update',
                          kwargs={'pk': cls.partnership.pk})
        cls.url_ko = reverse('partnerships:update',
                          kwargs={'pk': cls.partnership_ko.pk})

        # Years
        cls.year_0 = PartnershipYearFactory(partnership=cls.partnership, is_sms=True, is_smp=True, is_sta=True, is_stt=True)
        cls.year_1 = PartnershipYearFactory(partnership=cls.partnership, is_sms=True, is_sta=True)

        # Ucl
        cls.ucl_university = EntityFactory()
        cls.ucl_university_labo = EntityFactory()
        cls.university_offer = EducationGroupYearFactory()

        cls.data = {
            'comment': '',
            'partner': cls.partner.pk,
            'partner_entity': cls.partner_entity.pk,
            'supervisor': '',
            'ucl_university': cls.ucl_university.pk,
            'ucl_university_labo': cls.ucl_university_labo.pk,
            'university_offers': [cls.university_offer.pk,],
            'years-0-academic_year': '',
            'years-0-education_field': '',
            'years-0-education_level': '',
            'years-0-id': '',
            'years-0-partnership_type': '',
            'years-1-academic_year': '',
            'years-1-education_field': '',
            'years-1-education_level': '',
            'years-1-id': '',
            'years-1-partnership_type': '',
            'years-2-academic_year': '',
            'years-2-education_field': '',
            'years-2-education_level': '',
            'years-2-id': '',
            'years-2-partnership_type': '',
            'years-INITIAL_FORMS': '0',
            'years-MAX_NUM_FORMS': '1000',
            'years-MIN_NUM_FORMS': '0',
            'years-TOTAL_FORMS': '3',
        }

    def make_data(self, date, partnership):
        return {
            'start_date': date,
            'years-0-partnership': partnership.pk,
            'years-1-partnership': partnership.pk,
            'years-2-partnership': partnership.pk,
            **self.data,
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
        response = self.client.get(self.url)
        self.assertTemplateNotUsed(response, 'partnerships/partnership_update.html')

    def test_get_other_partnership_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/partnership_update.html')

    def test_get_out_of_date_as_adri(self):
        self.client.force_login(self.user_adri)
        data = self.make_data(self.date_ko.strftime('%d/%m/%y'), self.partnership)
        response = self.client.post(self.url_ko, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership_detail.html')

    def test_post(self):
        self.client.force_login(self.user_adri)
        data = self.make_data(
            (datetime.datetime.today() + datetime.timedelta(1)).strftime('%d/%m/%y'),
            self.partnership,
        )
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership_detail.html')

    def test_post_with_years(self):
        self.client.force_login(self.user_adri)
        data = self.make_data(
            (datetime.datetime.today() + datetime.timedelta(1)).strftime('%d/%m/%y'),
            self.partnership,
        )
        years_data = {
            'years-0-academic_year': self.year_0.academic_year.pk,
            'years-0-education_field': self.year_0.education_field,
            'years-0-education_level': self.year_0.education_level,
            'years-0-id': self.year_0.pk,
            'years-0-partnership_type': self.year_0.partnership_type,
            'years-0-is_sms': 'on' if self.year_0.is_sms else 'off',
            'years-0-is_smp': 'on' if self.year_0.is_smp else 'off',
            'years-0-is_sta': 'on' if self.year_0.is_sta else 'off',
            'years-0-is_stt': 'on' if self.year_0.is_stt else 'off',
            'years-1-academic_year': self.year_1.academic_year.pk,
            'years-1-education_field': self.year_1.education_field,
            'years-1-education_level': self.year_1.education_level,
            'years-1-id': self.year_1.pk,
            'years-1-partnership_type': self.year_1.partnership_type,
            'years-1-is_sms': 'on' if self.year_1.is_sms else 'off',
            'years-1-is_smp': 'on' if self.year_1.is_smp else 'off',
            'years-1-is_sta': 'on' if self.year_1.is_sta else 'off',
            'years-1-is_stt': 'on' if self.year_1.is_stt else 'off',
            'years-INITIAL_FORMS': '2',
        }
        data.update(years_data)
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership_detail.html')
