from django.test import TestCase
from django.urls import reverse

from base.tests.factories.entity_manager import EntityManagerFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.user import UserFactory
from partnership.models import ContactType
from partnership.tests.factories import PartnerFactory, PartnerTagFactory, PartnerTypeFactory
from reference.tests.factories.country import CountryFactory


class PartnerCreateViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.partner = PartnerFactory()
        cls.user = UserFactory()
        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PersonEntityFactory(entity=entity_version.entity, person__user=cls.user_adri)
        cls.user_gf = UserFactory()
        EntityManagerFactory(person__user=cls.user_gf)
        cls.contact_type = ContactType.objects.create(value='foobar')
        cls.country = CountryFactory()
        cls.url = reverse('partnerships:partners:create')

    def test_get_view_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partner_create.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_view_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partner_create.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_view_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/partner_create.html')

    def test_get_view_as_gf(self):
        self.client.force_login(self.user_gf)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/partner_create.html')

    def test_post(self):
        self.client.force_login(self.user_adri)
        data = {
            'partner-name': 'test',
            'partner-is_valid': 'on',
            'partner-start_date': '',
            'partner-end_date': '',
            'partner-partner_type': PartnerTypeFactory().pk,
            'partner-partner_code': 'test',
            'partner-pic_code': 'test',
            'partner-erasmus_code': 'test',
            'partner-is_ies': 'on',
            'partner-is_nonprofit': 'on',
            'partner-is_public': 'on',
            'partner-use_egracons': 'on',
            'partner-comment': 'test',
            'partner-phone': 'test',
            'partner-website': 'http://localhost:8000',
            'partner-email': 'test@test.test',
            'partner-tags': [PartnerTagFactory().id],
            'entities-TOTAL_FORMS': 1,
            'entities-INITIAL_FORMS': 0,
            'entities-MIN_NUM_FORMS': 0,
            'entities-MAX_NUM_FORMS': 1000,
            'entities-0-name': 'test',
            'entities-0-comment': 'test',
            'entities-0-address_name': 'test',
            'entities-0-address_address': 'test',
            'entities-0-address_postal_code': '13245',
            'entities-0-address_city': 'test',
            'entities-0-address_country': self.country.pk,
            'entities-0-contact_in_type': self.contact_type.pk,
            'entities-0-contact_in_title': 'mr',
            'entities-0-contact_in_last_name': 'test',
            'entities-0-contact_in_first_name': 'test',
            'entities-0-contact_in_function': 'test',
            'entities-0-contact_in_phone': 'test',
            'entities-0-contact_in_mobile_phone': 'test',
            'entities-0-contact_in_fax': 'test',
            'entities-0-contact_in_email': 'test@test.test',
            'entities-0-contact_out_type': self.contact_type.pk,
            'entities-0-contact_out_title': 'mr',
            'entities-0-contact_out_last_name': 'test',
            'entities-0-contact_out_first_name': 'test',
            'entities-0-contact_out_function': 'test',
            'entities-0-contact_out_phone': 'test',
            'entities-0-contact_out_mobile_phone': 'test',
            'entities-0-contact_out_fax': 'test',
            'entities-0-contact_out_email': 'test@test.test',
            'entities-0-parent': '',
        }
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partner_detail.html')
