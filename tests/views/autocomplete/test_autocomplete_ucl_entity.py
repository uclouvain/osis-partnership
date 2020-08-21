import json

from django.test import TestCase
from django.urls import reverse

from base.models.enums.entity_type import FACULTY, SCHOOL, SECTOR
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.user import UserFactory
from partnership.tests.factories import (
    PartnershipEntityManagerFactory, UCLManagementEntityFactory,
)


class UclEntityAutocompleteTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = PartnershipEntityManagerFactory().person.user
        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(entity=entity_version.entity, person__user=cls.user_adri)
        cls.user_gs = UserFactory()
        cls.user_gf = UserFactory()
        cls.user_other_gf = UserFactory()
        cls.other_gs = UserFactory()

        cls.url = reverse('partnerships:autocomplete:ucl_entity')

        # Ucl
        root = EntityVersionFactory(parent=None).entity
        cls.sector = EntityVersionFactory(
            entity_type=SECTOR,
            acronym='A',
            parent=root,
        ).entity
        cls.ucl_university = EntityVersionFactory(
            parent=cls.sector,
            entity_type=FACULTY,
            acronym='AA',
        ).entity
        UCLManagementEntityFactory(entity=cls.ucl_university)
        cls.ucl_university_labo = EntityVersionFactory(
            parent=cls.ucl_university,
            entity_type=SCHOOL,
            acronym='AA1',
        ).entity
        UCLManagementEntityFactory(entity=cls.ucl_university_labo)

        cls.ucl_university_2 = EntityVersionFactory(
            parent=cls.sector,
            entity_type=FACULTY,
            acronym='AB',
        ).entity
        UCLManagementEntityFactory(entity=cls.ucl_university_2)
        cls.ucl_university_labo_2 = EntityVersionFactory(
            parent=cls.ucl_university_2,
            entity_type=SCHOOL,
            acronym='AB1',
        ).entity
        UCLManagementEntityFactory(entity=cls.ucl_university_labo_2)

        sector_b = EntityVersionFactory(
            entity_type=SECTOR,
            acronym='B',
            parent=root,
        ).entity
        cls.ucl_university_3 = EntityVersionFactory(
            parent=sector_b,
            entity_type=FACULTY,
            acronym='BA',
        ).entity
        UCLManagementEntityFactory(entity=cls.ucl_university_3)
        cls.ucl_university_labo_3 = EntityVersionFactory(
            parent=cls.ucl_university_3,
            entity_type=SCHOOL,
            acronym='BA1',
        ).entity
        UCLManagementEntityFactory(entity=cls.ucl_university_labo_3)

        cls.data = {'forward': json.dumps({'partnership_type': 'MOBILITY'})}

        PartnershipEntityManagerFactory(person__user=cls.user_gs, entity=cls.sector)
        PartnershipEntityManagerFactory(person__user=cls.user_gf, entity=cls.ucl_university)
        PartnershipEntityManagerFactory(person__user=cls.user_other_gf, entity=cls.ucl_university_2)
        PartnershipEntityManagerFactory(person__user=cls.other_gs, entity=sector_b)
        PartnershipEntityManagerFactory(
            entity=EntityVersionFactory(parent=root, acronym='ADRI').entity,
            person__user=cls.user_adri,
        )

    def test_ucl_entity_autocomplete_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, self.data)
        results = response.json()['results']
        self.assertEqual(len(results), 0)

    def test_ucl_entity_autocomplete_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url, self.data)
        results = response.json()['results']
        self.assertEqual(len(results), 6)

    def test_ucl_entity_autocomplete_gf(self):
        self.client.force_login(self.user_gf)
        response = self.client.get(self.url, self.data)
        results = response.json()['results']
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['id'], str(self.ucl_university.pk))
        self.assertEqual(results[1]['id'], str(self.ucl_university_labo.pk))

    def test_ucl_entity_autocomplete_gs(self):
        self.client.force_login(self.user_gs)
        response = self.client.get(self.url, self.data)
        results = response.json()['results']
        self.assertEqual(len(results), 4)
        self.assertEqual(results[0]['id'], str(self.ucl_university.pk))
        self.assertEqual(results[1]['id'], str(self.ucl_university_labo.pk))
        self.assertEqual(results[2]['id'], str(self.ucl_university_2.pk))
        self.assertEqual(results[3]['id'], str(self.ucl_university_labo_2.pk))

    def test_ucl_entity_autocomplete_other_gs(self):
        self.client.force_login(self.other_gs)
        response = self.client.get(self.url, self.data)
        results = response.json()['results']
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['id'], str(self.ucl_university_3.pk))
        self.assertEqual(results[1]['id'], str(self.ucl_university_labo_3.pk))

    def test_ucl_entity_autocomplete_other_gf(self):
        self.client.force_login(self.user_other_gf)
        response = self.client.get(self.url, self.data)
        results = response.json()['results']
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['id'], str(self.ucl_university_2.pk))
        self.assertEqual(results[1]['id'], str(self.ucl_university_labo_2.pk))

    def test_other_type(self):
        self.client.force_login(self.user)
        response = self.client.get(
            self.url,
            data={'forward': json.dumps({'partnership_type': 'GENERAL'})},
        )
        results = response.json()['results']
        self.assertEqual(len(results), 10)
