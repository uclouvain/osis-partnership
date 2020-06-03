from unittest import TestCase

from partnership.converters import PartnershipTypeConverter
from partnership.models import PartnershipType


class ConverterTestCase(TestCase):
    def test_partnership_type_converter(self):
        converter = PartnershipTypeConverter()
        with self.assertRaises(ValueError):
            converter.to_python('foobar')

        self.assertEqual(
            converter.to_python('MOBILITY'), PartnershipType.MOBILITY,
        )
        self.assertEqual(
            converter.to_url(PartnershipType.MOBILITY), 'MOBILITY',
        )
