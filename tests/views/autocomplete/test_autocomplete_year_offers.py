import json

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.user import UserFactory
from partnership.tests.factories import (
    PartnershipYearEducationLevelFactory,
)


class YearOffersAutocompleteTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('partnerships:autocomplete:partnership_year_offers')

        # university_offer
        cls.university_offer = EducationGroupYearFactory(
            joint_diploma=True,
        )

        # education_level
        cls.education_level = PartnershipYearEducationLevelFactory()
        cls.education_level.education_group_types.add(
            cls.university_offer.education_group_type
        )

        cls.user = UserFactory()
        perm = Permission.objects.get(name='can_access_partnerships')
        cls.user.user_permissions.add(perm)

    def test_year_offer_autocomplete(self):
        self.client.force_login(self.user)

        # No forwarding, no result
        response = self.client.get(self.url)
        self.assertEqual(len(response.json()['results']), 0)

        def forward(fwd, **kwargs):
            return {'forward': json.dumps(fwd), **kwargs}

        response = self.client.get(self.url, forward({
            'education_levels': [self.education_level.pk],
            'entities': []
        }))
        self.assertEqual(len(response.json()['results']), 0)

        response = self.client.get(self.url, forward({
            'education_levels': [self.education_level.pk],
            'entities': [self.university_offer.management_entity.pk]
        }))
        self.assertEqual(len(response.json()['results']), 1)

        # 2 children on faculty AA
        response = self.client.get(self.url, forward({
            'education_levels': [self.education_level.pk],
            'entity': self.university_offer.management_entity.pk
        }, q=self.university_offer.title[:2]))
        self.assertEqual(len(response.json()['results']), 1)
