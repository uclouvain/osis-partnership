from django.test import TestCase

from base.models.entity_version_address import EntityVersionAddress
from partnership.templatetags.partnerships import address_one_line
from reference.models.country import Country


class TemplateTagsTestCase(TestCase):
    def test_address_one_line(self):
        self.assertEqual(address_one_line(None), '')
        european = EntityVersionAddress(
            street_number="10",
            street="Downing St.",
            city="London",
            country=Country.objects.create(name="United-Kingdom", iso_code='UK'),
        )
        self.assertEqual(
            address_one_line(european),
            "10 Downing St., London, UNITED-KINGDOM"
        )
        american = EntityVersionAddress(
            street="Golden Gate State Bridge",
            city="San Francisco",
            state="California",
            country=Country.objects.create(name="USA"),
        )
        self.assertEqual(
            address_one_line(american),
            "Golden Gate State Bridge, San Francisco, California, USA"
        )
