from django.test import TestCase
from django.urls import reverse

from base.models.enums.entity_type import FACULTY
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.user import UserFactory
from partnership.tests.factories import (
    PartnershipEntityManagerFactory,
    UCLManagementEntityFactory
)


class UCLManagementEntityCreateViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        faculty = EntityFactory()
        EntityVersionFactory(entity_type="FACULTY", entity=faculty)

        # Users
        cls.lambda_user = UserFactory()
        cls.adri_user = UserFactory()
        entity_version = EntityVersionFactory(acronym="ADRI")
        PartnershipEntityManagerFactory(entity=entity_version.entity, person__user=cls.adri_user)
        cls.gf_user = UserFactory()
        entity_manager = PartnershipEntityManagerFactory(person__user=cls.gf_user, entity=faculty)

        cls.url = reverse("partnerships:ucl_management_entities:create")

        # Data :
        cls.faculty = EntityFactory()
        EntityVersionFactory(entity=cls.faculty, entity_type=FACULTY)
        cls.entity = EntityFactory()
        cls.academic_responsible = PersonFactory()
        cls.administrative_responsible = PersonFactory()
        cls.contact_in_person = PersonFactory()
        cls.contact_out_person = PersonFactory()

        # Case for duplicate with faculty:
        UCLManagementEntityFactory(entity=cls.faculty)

        cls.data = {
            'academic_responsible': str(cls.academic_responsible.pk),
            'administrative_responsible': str(cls.administrative_responsible.pk),
            'contact_in_email': 'foo@foo.fr',
            'contact_in_person': str(cls.contact_in_person.pk),
            'contact_in_url': 'http://foo.fr/foo',
            'contact_out_email': 'bar@bar.fr',
            'contact_out_person': str(cls.contact_out_person.pk),
            'contact_out_url': 'http://bar.fr/bar',
            'entity': str(cls.entity.pk),
        }
        cls.template_create = 'partnerships/ucl_management_entities/uclmanagemententity_create.html'
        cls.template_list = 'partnerships/ucl_management_entities/uclmanagemententity_list.html'

    def test_get_view_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, self.template_create)
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_view_authenticated(self):
        self.client.force_login(self.lambda_user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, self.template_create)
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_view_gf(self):
        self.client.force_login(self.gf_user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, self.template_create)
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_view_adri(self):
        self.client.force_login(self.adri_user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, self.template_create)

    def test_post_anonymous(self):
        response = self.client.post(self.url, data=self.data, follow=True)
        self.assertTemplateNotUsed(response, self.template_list)
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_post_lambda_user(self):
        self.client.force_login(self.lambda_user)
        response = self.client.post(self.url, data=self.data, follow=True)
        self.assertTemplateNotUsed(response, self.template_list)
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_post_gf_user(self):
        self.client.force_login(self.gf_user)
        response = self.client.post(self.url, data=self.data, follow=True)
        self.assertTemplateNotUsed(response, self.template_list)
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_post_adri(self):
        self.client.force_login(self.adri_user)
        response = self.client.post(self.url, data=self.data, follow=True)
        self.assertTemplateUsed(response, self.template_list)

    def test_post_adri_no_value(self):
        self.client.force_login(self.adri_user)
        response = self.client.post(self.url, data={}, follow=True)
        self.assertTemplateNotUsed(response, self.template_list)
        self.assertTemplateUsed(response, self.template_create)

    def test_post_adri_duplicate_faculty_null_entity(self):
        self.client.force_login(self.adri_user)
        data = self.data
        data['entity'] = self.faculty.pk
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateNotUsed(response, self.template_list)
        self.assertTemplateUsed(response, self.template_create)
