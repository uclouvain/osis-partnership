from django.test import TestCase
from django.urls import reverse

from base.models.enums.entity_type import FACULTY
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.user import UserFactory
from partnership.models import UCLManagementEntity
from partnership.tests.factories import (PartnershipEntityManagerFactory,
                                         PartnershipFactory,
                                         UCLManagementEntityFactory)


class UCLManagementEntityUpdateViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        sector = EntityFactory()
        faculty = EntityFactory()
        EntityVersionFactory(entity=faculty, parent=sector, entity_type=FACULTY)
        other_faculty = EntityFactory()
        EntityVersionFactory(entity_type="FACULTY", entity=faculty)
        EntityVersionFactory(entity_type="FACULTY", entity=other_faculty)

        cls.ucl_management_entity = UCLManagementEntityFactory(faculty=faculty)
        cls.other_ucl_management_entity = UCLManagementEntityFactory(faculty=other_faculty)
        cls.ucl_management_entity_linked = UCLManagementEntityFactory(faculty=other_faculty, entity=None)
        PartnershipFactory(ucl_university=other_faculty, ucl_university_labo=None)

        # Users
        cls.lambda_user = UserFactory()
        cls.adri_user = UserFactory()
        entity_version = EntityVersionFactory(acronym="ADRI")
        PartnershipEntityManagerFactory(entity=entity_version.entity, person__user=cls.adri_user)
        cls.gs_user = UserFactory()
        PartnershipEntityManagerFactory(person__user=cls.gs_user, entity=sector)
        cls.gf_user = UserFactory()
        entity_manager = PartnershipEntityManagerFactory(person__user=cls.gf_user, entity=faculty)
        cls.other_gf_user = UserFactory()
        PartnershipEntityManagerFactory(person__user=cls.other_gf_user, entity=other_faculty)

        cls.url = reverse(
            "partnerships:ucl_management_entities:update",
            kwargs={'pk': cls.ucl_management_entity.pk},
        )
        cls.other_url = reverse(
            "partnerships:ucl_management_entities:update",
            kwargs={'pk': cls.other_ucl_management_entity.pk},
        )
        cls.linked_url = reverse(
            "partnerships:ucl_management_entities:update",
            kwargs={"pk": cls.ucl_management_entity_linked.pk},
        )

        # Data :
        cls.faculty = EntityFactory()
        EntityVersionFactory(entity=cls.faculty, entity_type=FACULTY)
        cls.entity = EntityFactory()
        cls.academic_responsible = PersonFactory()
        cls.administrative_responsible = PersonFactory()
        cls.contact_in_person = PersonFactory()
        cls.contact_out_person = PersonFactory()

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
            'faculty': str(cls.faculty.pk),
        }

    def test_get_view_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/ucl_management_entities/uclmanagemententity_update.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_view_authenticated(self):
        self.client.force_login(self.lambda_user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/ucl_management_entities/uclmanagemententity_update.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_view_gf_user(self):
        self.client.force_login(self.gf_user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/ucl_management_entities/uclmanagemententity_update.html')

    def test_get_view_gs_user(self):
        self.client.force_login(self.gs_user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/ucl_management_entities/uclmanagemententity_update.html')

    def test_get_view_other_gf_user(self):
        self.client.force_login(self.other_gf_user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/ucl_management_entities/uclmanagemententity_update.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_view_adri_user(self):
        self.client.force_login(self.adri_user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/ucl_management_entities/uclmanagemententity_update.html')

    def test_post_view_anonymous(self):
        response = self.client.post(self.url, data=self.data, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/ucl_management_entities/uclmanagemententity_list.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_post_view_authenticated(self):
        self.client.force_login(self.lambda_user)
        response = self.client.post(self.url, data=self.data, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/ucl_management_entities/uclmanagemententity_list.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_post_view_gf_user(self):
        self.client.force_login(self.gf_user)
        data = self.data.copy()
        data['academic_responsible'] = self.ucl_management_entity.academic_responsible.pk
        data['administrative_responsible'] = self.ucl_management_entity.administrative_responsible.pk
        data['entity'] = self.ucl_management_entity.entity.pk
        data['faculty'] = self.ucl_management_entity.faculty.pk
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(
            response,
            'partnerships/ucl_management_entities/uclmanagemententity_list.html'
        )
        ucl_management_entity = UCLManagementEntity.objects.get(pk=self.ucl_management_entity.pk)
        self.assertEqual(
            ucl_management_entity.academic_responsible.pk,
            data['academic_responsible'],
        )
        self.assertEqual(
            ucl_management_entity.administrative_responsible.pk,
            data['administrative_responsible']
        )
        self.assertEqual(
            ucl_management_entity.entity.pk,
            data['entity'],
        )
        self.assertEqual(
            ucl_management_entity.faculty.pk,
            data['faculty'],
        )
        self.assertEqual(
            ucl_management_entity.contact_in_email,
            data['contact_in_email']
        )
        self.assertEqual(
            str(ucl_management_entity.contact_in_person.pk),
            data['contact_in_person'],
        )
        self.assertEqual(
            ucl_management_entity.contact_in_url,
            data['contact_in_url']
        )
        self.assertEqual(
            ucl_management_entity.contact_out_email,
            data['contact_out_email']
        )
        self.assertEqual(
            str(ucl_management_entity.contact_out_person.pk),
            data['contact_out_person']
        )
        self.assertEqual(
            ucl_management_entity.contact_out_url,
            data['contact_out_url']
        )

    def test_post_view_gs_user(self):
        self.client.force_login(self.gs_user)
        data = self.data.copy()
        data['academic_responsible'] = self.ucl_management_entity.academic_responsible.pk
        data['administrative_responsible'] = self.ucl_management_entity.administrative_responsible.pk
        data['entity'] = self.ucl_management_entity.entity.pk
        data['faculty'] = self.ucl_management_entity.faculty.pk
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(
            response,
            'partnerships/ucl_management_entities/uclmanagemententity_list.html'
        )
        ucl_management_entity = UCLManagementEntity.objects.get(pk=self.ucl_management_entity.pk)
        self.assertEqual(
            ucl_management_entity.academic_responsible.pk,
            data['academic_responsible'],
        )
        self.assertEqual(
            ucl_management_entity.administrative_responsible.pk,
            data['administrative_responsible']
        )
        self.assertEqual(
            ucl_management_entity.entity.pk,
            data['entity'],
        )
        self.assertEqual(
            ucl_management_entity.faculty.pk,
            data['faculty'],
        )
        self.assertEqual(
            ucl_management_entity.contact_in_email,
            data['contact_in_email']
        )
        self.assertEqual(
            str(ucl_management_entity.contact_in_person.pk),
            data['contact_in_person'],
        )
        self.assertEqual(
            ucl_management_entity.contact_in_url,
            data['contact_in_url']
        )
        self.assertEqual(
            ucl_management_entity.contact_out_email,
            data['contact_out_email']
        )
        self.assertEqual(
            str(ucl_management_entity.contact_out_person.pk),
            data['contact_out_person']
        )
        self.assertEqual(
            ucl_management_entity.contact_out_url,
            data['contact_out_url']
        )


    def test_post_view_other_gf_user(self):
        self.client.force_login(self.other_gf_user)
        response = self.client.post(self.url, data=self.data, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/ucl_management_entities/uclmanagemententity_list.html')

    def test_post_view_other_gf_as_gs_user(self):
        self.client.force_login(self.gs_user)
        response = self.client.post(self.other_url, data=self.data, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/ucl_management_entities/uclmanagemententity_list.html')

    def test_post_adri_no_value(self):
        self.client.force_login(self.adri_user)
        response = self.client.post(self.url, data={}, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/ucl_management_entities/uclmanagemententity_list.html')
        self.assertTemplateUsed(response, 'partnerships/ucl_management_entities/uclmanagemententity_update.html')

    def test_post_view_adri_user(self):
        self.client.force_login(self.adri_user)
        response = self.client.post(self.url, data=self.data, follow=True)
        self.assertTemplateUsed(
            response,
            'partnerships/ucl_management_entities/uclmanagemententity_list.html'
        )
        ucl_management_entity = UCLManagementEntity.objects.get(pk=self.ucl_management_entity.pk)
        self.assertEqual(
            str(ucl_management_entity.academic_responsible.pk),
            self.data['academic_responsible']
        )
        self.assertEqual(
            str(ucl_management_entity.administrative_responsible.pk),
            self.data['administrative_responsible']
        )
        self.assertEqual(
            ucl_management_entity.contact_in_email,
            self.data['contact_in_email']
        )
        self.assertEqual(
            str(ucl_management_entity.contact_in_person.pk),
            self.data['contact_in_person']
        )
        self.assertEqual(
            ucl_management_entity.contact_in_url,
            self.data['contact_in_url']
        )
        self.assertEqual(
            ucl_management_entity.contact_out_email,
            self.data['contact_out_email']
        )
        self.assertEqual(
            str(ucl_management_entity.contact_out_person.pk),
            self.data['contact_out_person']
        )
        self.assertEqual(
            ucl_management_entity.contact_out_url,
            self.data['contact_out_url']
        )
        self.assertEqual(
            str(ucl_management_entity.faculty.pk),
            self.data['faculty']
        )
        self.assertEqual(
            str(ucl_management_entity.entity.pk),
            self.data['entity']
        )

    def test_post_view_with_linked_adri_user(self):
        self.client.force_login(self.adri_user)
        data = self.data.copy()
        del data['entity']
        del data['faculty']
        response = self.client.post(self.linked_url, data=data, follow=True)
        self.assertTemplateUsed(
            response,
            'partnerships/ucl_management_entities/uclmanagemententity_list.html'
        )
        ucl_management_entity = UCLManagementEntity.objects.get(pk=self.ucl_management_entity_linked.pk)
        self.assertEqual(
            str(ucl_management_entity.academic_responsible.pk),
            str(data['academic_responsible'])
        )
        self.assertEqual(
            str(ucl_management_entity.administrative_responsible.pk),
            str(data['administrative_responsible'])
        )
        self.assertEqual(
            ucl_management_entity.contact_in_email,
            data['contact_in_email']
        )
        self.assertEqual(
            str(ucl_management_entity.contact_in_person.pk),
            data['contact_in_person']
        )
        self.assertEqual(
            ucl_management_entity.contact_in_url,
            data['contact_in_url']
        )
        self.assertEqual(
            ucl_management_entity.contact_out_email,
            data['contact_out_email']
        )
        self.assertEqual(
            str(ucl_management_entity.contact_out_person.pk),
            data['contact_out_person']
        )
        self.assertEqual(
            ucl_management_entity.contact_out_url,
            data['contact_out_url']
        )
