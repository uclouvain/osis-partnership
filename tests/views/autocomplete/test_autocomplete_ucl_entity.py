from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from base.models.enums.entity_type import FACULTY, SCHOOL, SECTOR
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.user import UserFactory
from partnership.tests.factories import (
    PartnershipEntityManagerFactory, UCLManagementEntityFactory,
)


class UclEntityAutocompleteTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        PersonFactory(user=cls.user)
        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(entity=entity_version.entity, person__user=cls.user_adri)
        cls.user_gs = UserFactory()
        cls.user_gf = UserFactory()
        cls.user_other_gf = UserFactory()

        perm = Permission.objects.get(name='can_access_partnerships')
        cls.user.user_permissions.add(perm)
        cls.user_adri.user_permissions.add(perm)
        cls.user_gs.user_permissions.add(perm)
        cls.user_gf.user_permissions.add(perm)
        cls.user_other_gf.user_permissions.add(perm)

        cls.url = reverse('partnerships:autocomplete:ucl_entity')

        # Ucl
        sector = EntityFactory()
        EntityVersionFactory(
            entity=sector,
            entity_type=SECTOR,
            acronym='A',
        )
        cls.ucl_university = EntityFactory()
        EntityVersionFactory(
            entity=cls.ucl_university,
            parent=sector,
            entity_type=FACULTY,
            acronym='A1',
        )
        cls.ucl_university_labo = EntityFactory()
        EntityVersionFactory(
            entity=cls.ucl_university_labo,
            parent=cls.ucl_university,
            entity_type=SCHOOL,
            acronym='A11',
        )
        UCLManagementEntityFactory(entity=cls.ucl_university_labo)
        cls.ucl_university_not_choice = EntityFactory()
        EntityVersionFactory(
            entity=cls.ucl_university_not_choice,
            entity_type=FACULTY,
            acronym='B1',
        )
        cls.ucl_university_labo_not_choice = EntityFactory()
        EntityVersionFactory(
            entity=cls.ucl_university_labo_not_choice,
            parent=cls.ucl_university_not_choice,
            entity_type=SCHOOL,
            acronym='B11',
        )

        PartnershipEntityManagerFactory(person__user=cls.user_gs, entity=sector)
        PartnershipEntityManagerFactory(person__user=cls.user_gf, entity=cls.ucl_university)
        PartnershipEntityManagerFactory(person__user=cls.user_other_gf, entity=cls.ucl_university)

    def test_ucl_entity_autocomplete_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        results = response.json()['results']
        self.assertEqual(len(results), 0)

    def test_ucl_entity_autocomplete_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url)
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], str(self.ucl_university_labo.pk))

        # Add a management entity on faculty, and we should have 2
        UCLManagementEntityFactory(entity=self.ucl_university)
        response = self.client.get(self.url)
        results = response.json()['results']
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['id'], str(self.ucl_university.pk))
        self.assertEqual(results[1]['id'], str(self.ucl_university_labo.pk))

    def test_ucl_entity_autocomplete_gf(self):
        self.client.force_login(self.user_gf)
        response = self.client.get(self.url)
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], str(self.ucl_university_labo.pk))

        # Add a management entity on faculty, and we should have 2
        UCLManagementEntityFactory(entity=self.ucl_university)
        response = self.client.get(self.url)
        results = response.json()['results']
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['id'], str(self.ucl_university.pk))
        self.assertEqual(results[1]['id'], str(self.ucl_university_labo.pk))

    def test_ucl_entity_autocomplete_gs(self):
        self.client.force_login(self.user_gs)
        response = self.client.get(self.url)
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], str(self.ucl_university_labo.pk))

    def test_ucl_entity_autocomplete_other_gf(self):
        self.client.force_login(self.user_other_gf)
        response = self.client.get(self.url)
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], str(self.ucl_university_labo.pk))
