from django.test import TestCase
from django.urls import reverse

from base.tests.factories.user import UserFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.entity_manager import EntityManagerFactory
from base.tests.factories.person_entity import PersonEntityFactory
from partnership.tests.factories import (
    PartnershipFactory, PartnerFactory,
    PartnershipYearFactory)

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
        cls.partner = PartnerFactory()
        cls.partner_gf = PartnerFactory(author=cls.user_gf)
        cls.partnership = PartnershipFactory(partner=cls.partner)
        cls.url = reverse('partnerships:partnership_update', kwargs={'pk': cls.partnership.pk})

        # Years
        cls.year1 = PartnershipYearFactory()
        cls.year2 = PartnershipYearFactory()
    
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
        self.assertTemplateUsed(response, 'partnerships/partnership_update.html')

    def test_get_other_partnership_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/partnership_update.html')
        
    def test_post(self):
        self.client.force_login(self.user_adri)
        data = {

        }
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership_detail.html')
