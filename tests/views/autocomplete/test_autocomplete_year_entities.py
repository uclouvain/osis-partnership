import json

from django.test import TestCase
from django.urls import reverse

from base.models.enums.entity_type import (
    DOCTORAL_COMMISSION,
    FACULTY,
    SCHOOL,
    SECTOR,
)
from base.models.enums.organization_type import MAIN
from base.tests.factories.entity import EntityFactory
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
        cls.sector = EntityFactory(organization__type=MAIN)
        EntityVersionFactory(
            entity=cls.sector,
            entity_type=SECTOR,
            acronym='A',
        )
        cls.commission = EntityFactory(organization__type=MAIN)
        EntityVersionFactory(
            entity=cls.commission,
            parent=cls.sector,
            entity_type=DOCTORAL_COMMISSION,
            acronym='DA',
        )
        cls.ucl_university = EntityFactory(organization__type=MAIN)
        EntityVersionFactory(
            entity=cls.ucl_university,
            parent=cls.sector,
            entity_type=FACULTY,
            acronym='AA',
        )
        cls.labo = EntityFactory(organization__type=MAIN)
        EntityVersionFactory(
            entity=cls.labo,
            parent=cls.ucl_university,
            entity_type=SCHOOL,
            acronym='AA1',
        )

        cls.labo_2 = EntityFactory(organization__type=MAIN)
        EntityVersionFactory(
            entity=cls.labo_2,
            parent=cls.ucl_university,
            entity_type=SCHOOL,
            acronym='AA2',
        )

        cls.ucl_university_2 = EntityFactory(organization__type=MAIN)
        EntityVersionFactory(
            entity=cls.ucl_university_2,
            parent=cls.sector,
            entity_type=FACULTY,
            acronym='AB',
        )
        cls.labo_2 = EntityFactory(organization__type=MAIN)
        EntityVersionFactory(
            entity=cls.labo_2,
            parent=cls.ucl_university_2,
            entity_type=SCHOOL,
            acronym='AB1',
        )

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
