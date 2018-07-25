from django.test import TestCase
from django.urls import reverse

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_manager import EntityManagerFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.user import UserFactory
from partnership.models import ContactType
from partnership.tests.factories import PartnerTagFactory, PartnerTypeFactory, PartnerFactory, PartnershipTagFactory
from reference.tests.factories.country import CountryFactory


class PartnershipCreateViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PersonEntityFactory(entity=entity_version.entity, person__user=cls.user_adri)
        cls.user_gf = UserFactory()
        EntityManagerFactory(person__user=cls.user_gf)
        cls.country = CountryFactory()
        cls.url = reverse('partnerships:create')

    def test_get_view_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partnership_create.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_view_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partnership_create.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_view_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership_create.html')

    def test_get_view_as_gf(self):
        self.client.force_login(self.user_gf)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership_create.html')

    def test_post(self):
        self.client.force_login(self.user_adri)
        partner = PartnerFactory()
        university = EntityFactory()
        university_labo = EntityFactory()
        offer = EducationGroupYearFactory()
        supervisor = PersonFactory()
        tag1 = PartnershipTagFactory()
        tag2 = PartnershipTagFactory()
        academic_year1 = AcademicYearFactory()
        academic_year2 = AcademicYearFactory()
        data = {
            'partner': partner.pk,
            'partner_entity': partner.entities.first().pk,
            'start_date': '19/07/2018',
            'ucl_university': university.pk,
            'ucl_university_labo': university_labo.pk,
            'university_offers': [offer.pk],
            'supervisor': supervisor.pk,
            'tags': [tag1.pk, tag2.pk],
            'comment': 'commentaire',
            'years-TOTAL_FORMS': '2',
            'years-INITIAL_FORMS': '0',
            'years-MIN_NUM_FORMS': '0',
            'years-MAX_NUM_FORMS': '1000',
            'years-0-id': '',
            'years-0-partnership': '',
            'years-0-academic_year': academic_year1.pk,
            'years-0-education_field': '0110',
            'years-0-education_level': 'ISCED-5',
            'years-0-partnership_type': 'intention',
            'years-0-is_sms': 'on',
            'years-0-is_smp': 'on',
            'years-1-id': '',
            'years-1-partnership': '',
            'years-1-academic_year': academic_year2.pk,
            'years-1-education_field': '0111',
            'years-1-education_level': 'ISCED-6',
            'years-1-partnership_type': 'cadre',
            'years-1-is_sta': 'on',
            'years-1-is_stt': 'on',
        }
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership_detail.html')
