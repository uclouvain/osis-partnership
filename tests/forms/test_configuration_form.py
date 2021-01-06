from django.test import TestCase

from base.tests.factories.academic_year import (
    AcademicYearFactory,
    get_current_year,
)
from partnership.forms import PartnershipConfigurationForm


class ConfigurationFormTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        AcademicYearFactory.produce(
            number_past=1,
            number_future=3,
        )

    def test_configuration_form(self):
        year = get_current_year()
        form = PartnershipConfigurationForm()
        for field in ['partnership_creation_update_min_year', 'partnership_api_year']:
            choices = list(form.fields[field].choices)
            # Should have null + 3 years
            self.assertEqual(len(choices), 4)
            # Should be current year first
            self.assertIn(str(year), choices[1][1])
