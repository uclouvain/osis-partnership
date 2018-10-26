import tempfile
from django.test import TestCase
from django.urls import reverse
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.user import UserFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person_entity import PersonEntityFactory
from reference.tests.factories.country import CountryFactory
from partnership.tests.factories import FinancingFactory
from partnership.models import Financing


class FinancingsImportViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        file_content = "AL;foo;http://foo.com\nAF;bar;http://bar.com"
        cls.filename_1 = tempfile.mkstemp()[1]
        cls.filename_2 = tempfile.mkstemp()[1]
        cls.country_1 = CountryFactory()
        cls.country_2 = CountryFactory()
        cls.country_3 = CountryFactory()
        cls.country_4 = CountryFactory()
        with open(cls.filename_1, 'w') as f:
            f.write('{};foo;http://foo.com\n'.format(cls.country_1.iso_code))
            f.write('{};bar;http://bar.com\n'.format(cls.country_2.iso_code))
            f.write('{};foo;http://foo.com\n'.format(cls.country_3.iso_code))
        with open(cls.filename_2, 'w') as f:
            f.write('{};foo;http://foobis.com\n'.format(cls.country_4.iso_code))
        cls.user = UserFactory()
        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PersonEntityFactory(entity=entity_version.entity, person__user=cls.user_adri)
        cls.academic_year = AcademicYearFactory()
        cls.url = reverse('partnerships:financings:import')

    def test_import_as_anonymous(self):
        with open(self.filename_1, 'r') as f:
            data = {
                'csv_file': f,
                'import_academic_year': self.academic_year.pk,
            }
            response = self.client.post(self.url, data, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/financings/financing_list.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_import_as_user(self):
        self.client.force_login(self.user)
        with open(self.filename_1, 'r') as f:
            data = {
                'csv_file': f,
                'import_academic_year': self.academic_year.pk,
            }
            response = self.client.post(self.url, data, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/financings/financing_list.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_import_as_adri(self):
        self.client.force_login(self.user_adri)
        with open(self.filename_1, 'r') as f:
            data = {
                'csv_file': f,
                'import_academic_year': self.academic_year.pk,
            }
            response = self.client.post(self.url, data, follow=True)
        self.assertEqual(Financing.objects.filter(academic_year=self.academic_year).count(), 2)
        with open(self.filename_2, 'r') as f:
            data = {
                'csv_file': f,
                'import_academic_year': self.academic_year.pk,
            }
            response = self.client.post(self.url, data, follow=True)
        financing = Financing.objects.get(name='foo')
        self.assertEqual(financing.url, 'http://foobis.com')
        self.assertIn(self.country_1, financing.countries.all())
        self.assertNotIn(self.country_2, financing.countries.all())
        self.assertIn(self.country_3, financing.countries.all())
        self.assertIn(self.country_4, financing.countries.all())
        self.assertTemplateUsed(response, 'partnerships/financings/financing_list.html')

    def test_import_as_adri_invalid(self):
        self.client.force_login(self.user_adri)
        with open(self.filename_1, 'r') as f:
            data = {
                'import_academic_year': self.academic_year.pk,
            }
            response = self.client.post(self.url, data, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/financings/financing_list.html')
        self.assertTemplateUsed(response, 'partnerships/financings/financing_import.html')
