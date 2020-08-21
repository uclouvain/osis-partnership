import json

from django.test import TestCase
from django.urls import reverse

from base.models.enums.entity_type import (
    DOCTORAL_COMMISSION,
    FACULTY,
    SCHOOL,
    SECTOR,
)
from base.tests.factories.entity_version import EntityVersionFactory
from partnership.models import PartnershipType
from partnership.tests.factories import (
    PartnershipEntityManagerFactory,
    PartnershipYearFactory,
)


class YearEntitiesAutocompleteTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = PartnershipEntityManagerFactory().person.user

        cls.url = reverse(
            'partnerships:autocomplete:partnership_year_entities'
        )
        cls.filter_url = reverse(
            'partnerships:autocomplete:years_entity_filter'
        )

        # Ucl
        root = EntityVersionFactory(parent=None).entity
        cls.sector = EntityVersionFactory(
            entity_type=SECTOR,
            acronym='A',
            parent=root,
        ).entity
        cls.commission = EntityVersionFactory(
            parent=cls.sector,
            entity_type=DOCTORAL_COMMISSION,
            acronym='DA',
        ).entity
        cls.ucl_university = EntityVersionFactory(
            parent=cls.sector,
            entity_type=FACULTY,
            acronym='AA',
        ).entity
        cls.labo = EntityVersionFactory(
            parent=cls.ucl_university,
            entity_type=SCHOOL,
            acronym='AA1',
        ).entity

        cls.labo_2 = EntityVersionFactory(
            parent=cls.ucl_university,
            entity_type=SCHOOL,
            acronym='AA2',
        ).entity

        cls.ucl_university_2 = EntityVersionFactory(
            parent=cls.sector,
            entity_type=FACULTY,
            acronym='AB',
        ).entity
        cls.labo_2 = EntityVersionFactory(
            parent=cls.ucl_university_2,
            entity_type=SCHOOL,
            acronym='AB1',
        ).entity

    def test_year_entities_autocomplete(self):
        self.client.force_login(self.user)

        # No entity, no result
        response = self.client.get(self.url)
        self.assertEqual(len(response.json()['results']), 0)

        def forward(entity, **kwargs):
            return {'forward': json.dumps({'entity': entity.pk}), **kwargs}

        # 2 children on faculty AA
        response = self.client.get(self.url, forward(self.ucl_university))
        self.assertEqual(len(response.json()['results']), 2)

        # 2 sibling on labo AA1
        response = self.client.get(self.url, forward(self.labo))
        self.assertEqual(len(response.json()['results']), 2)

        # 1 child on faculty AB
        response = self.client.get(self.url, forward(self.ucl_university_2))
        self.assertEqual(len(response.json()['results']), 1)

        # self on labo AB1
        response = self.client.get(self.url, forward(self.labo_2))
        self.assertEqual(len(response.json()['results']), 1)

        # with query on AA
        response = self.client.get(self.url, forward(self.labo, q='AA'))
        self.assertEqual(len(response.json()['results']), 2)

    def test_year_entities_autocomplete_doctorate(self):
        self.client.force_login(self.user)

        # with doctorate type specified, should return doctorate commissions
        response = self.client.get(self.url, {'forward': json.dumps({
            'entity': self.sector.pk,
            'partnership_type': PartnershipType.DOCTORATE.name,
        })})
        self.assertEqual(len(response.json()['results']), 1)

    def test_filter(self):
        self.client.force_login(self.user)

        # No entity, no result
        response = self.client.get(self.filter_url)
        self.assertEqual(len(response.json()['results']), 0)

        def forward(entity, **kwargs):
            return {'forward': json.dumps({'ucl_entity': entity.pk}), **kwargs}

        # No partnerhsip, no result
        response = self.client.get(self.filter_url, forward(self.ucl_university))
        self.assertEqual(len(response.json()['results']), 0)

        # Partnerhsip, result
        partnerhsip_year = PartnershipYearFactory()
        partnerhsip_year.entities.add(self.labo)
        response = self.client.get(self.filter_url, forward(self.ucl_university))
        self.assertEqual(len(response.json()['results']), 1)
