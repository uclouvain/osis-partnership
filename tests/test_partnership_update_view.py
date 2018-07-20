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
        cls.partner_entity = PartnerEntityFactory()
        cls.partner = PartnerFactory()
        cls.partner_gf = PartnerFactory(author=cls.user_gf)
        cls.partnership = PartnershipFactory(partner=cls.partner,
                                             partner_entity=cls.partner_entity)
        cls.url = reverse('partnerships:partnership_update',
                          kwargs={'pk': cls.partnership.pk})

        # Years
        cls.year1 = PartnershipYearFactory()
        cls.year2 = PartnershipYearFactory()

        # Ucl
        cls.ucl_university = EntityFactory()
        cls.ucl_university_labo = EntityFactory()
        cls.university_offers = EducationGroupYearFactory()

    def test_get_partnership_as_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partnership_update.html')
        self.assertTemplateUsed(response, 'registeration/login.html')
        
    def test_get_partnership_as_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership_update.html')

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
        
    def test_post(self):
        self.client.force_login(self.user_adri)
        data = {
            'comment': '',
            'partner': self.partner.pk,
            'partner_entity': self.partner_entity.pk,
            'start_date': (datetime.datetime.today() + datetime.timedelta(1)).strftime('%d/%m/%y'),
            'supervisor': '',
            'ucl_university': self.ucl_university.pk,
            'ucl_university_labo': self.ucl_university_labo.pk,
            'university_offers': [self.university_offers.pk,],
            'years-0-academic_year': '',
            'years-0-education_field': '',
            'years-0-education_level': '',
            'years-0-id': '',
            'years-0-partnership': self.partnership.pk,
            'years-0-partnership_type': '',
            'years-1-academic_year': '',
            'years-1-education_field': '',
            'years-1-education_level': '',
            'years-1-id': '',
            'years-1-partnership': self.partnership.pk,
            'years-1-partnership_type': '',
            'years-2-academic_year': '',
            'years-2-education_field': '',
            'years-2-education_level': '',
            'years-2-id': '',
            'years-2-partnership': self.partnership.pk,
            'years-2-partnership_type': '',
            'years-INITIAL_FORMS': '0',
            'years-MAX_NUM_FORMS': '1000',
            'years-MIN_NUM_FORMS': '0',
            'years-TOTAL_FORMS': '3',
        }
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership_detail.html')
