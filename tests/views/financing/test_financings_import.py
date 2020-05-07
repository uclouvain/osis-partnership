import tempfile

from django.test import TestCase
from django.urls import reverse

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.user import UserFactory
from partnership.models import Financing, FundingType
from partnership.tests.factories import (
    FundingProgramFactory, FundingSourceFactory,
    PartnershipEntityManagerFactory,
)
from reference.tests.factories.country import CountryFactory


class FinancingsImportViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.filename_1 = tempfile.mkstemp(suffix='.csv')[1]
        cls.filename_2 = tempfile.mkstemp(suffix='.csv')[1]
        cls.filename_3 = tempfile.mkstemp(suffix='.badext')[1]
        cls.country_1 = CountryFactory(name='country_1', iso_code='C1')
        cls.country_2 = CountryFactory(name='country_2', iso_code='C2')
        cls.country_3 = CountryFactory(name='country_3', iso_code='C3')
        cls.country_4 = CountryFactory(name='country_4', iso_code='C4')
        FundingSourceFactory(name='Source1')
        FundingSourceFactory(name='Source2')
        FundingProgramFactory(name='ProgramA')
        FundingProgramFactory(name='ProgramB')
        FundingProgramFactory(name='ProgramC')

        with open(cls.filename_1, 'w') as f:
            f.write('country_name;country;name;url;program;source\n')
            f.write('{0.name};{0.iso_code};foo;http://foo.com;ProgramB;Source2\n'.format(cls.country_1))
            f.write('{0.name};{0.iso_code};bar;http://bar.com;ProgramC;Source2\n'.format(cls.country_2))
            f.write('{0.name};{0.iso_code};foo;http://foo.com;ProgramA;Source1\n'.format(cls.country_3))
            # bad country
            f.write('FOO;ZZ;baz;http://baz.com;ProgramD;Source1\n')
            # bad program
            f.write('{0.name};{0.iso_code};foo;http://foo.com;bad program;Source1\n'.format(cls.country_3))
            # bad url
            f.write('{0.name};{0.iso_code};foo;badurl;ProgramA;Source1\n'.format(cls.country_3))
            # no name
            f.write('{0.name};{0.iso_code};;badurl;ProgramA;Source1\n'.format(cls.country_2))

        with open(cls.filename_2, 'w') as f:
            f.write('country_name;country;name;url;program;source\n')
            f.write('{0.name};{0.iso_code};foo;http://foobis.com;ProgramA;Source1\n'.format(cls.country_4))

        with open(cls.filename_3, 'w') as f:
            f.writelines(['foo', 'bar'])

        cls.user = UserFactory()
        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(entity=entity_version.entity, person__user=cls.user_adri)
        cls.academic_year = AcademicYearFactory()
        cls.url = reverse('partnerships:financings:import')

    def submit_scv(self, file):
        with open(file, 'r') as f:
            data = {
                'csv_file': f,
                'import_academic_year': self.academic_year.pk,
            }
            return self.client.post(self.url, data, follow=True)

    def test_import_as_anonymous(self):
        response = self.submit_scv(self.filename_1)
        self.assertTemplateNotUsed(response, 'partnerships/financings/financing_list.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_import_as_user(self):
        self.client.force_login(self.user)
        response = self.submit_scv(self.filename_1)
        self.assertTemplateNotUsed(response, 'partnerships/financings/financing_list.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_import_as_adri(self):
        self.client.force_login(self.user_adri)
        self.submit_scv(self.filename_1)
        self.assertEqual(Financing.objects.filter(academic_year=self.academic_year).count(), 2)
        funding = FundingType.objects.get(name='foo')
        self.assertEqual(funding.url, 'http://foo.com')

        financing = Financing.objects.get(type__name='foo')
        countries = financing.countries.all()
        self.assertIn(self.country_1, countries)
        self.assertNotIn(self.country_2, countries)
        self.assertIn(self.country_3, countries)

        response = self.submit_scv(self.filename_2)
        funding = FundingType.objects.get(name='foo')
        self.assertEqual(funding.url, 'http://foobis.com')

        financing = Financing.objects.get(type__name='foo')
        countries = financing.countries.all()
        self.assertNotIn(self.country_1, countries)
        self.assertIn(self.country_4, countries)
        self.assertTemplateUsed(response, 'partnerships/financings/financing_list.html')

    def test_import_as_adri_invalid(self):
        self.client.force_login(self.user_adri)
        data = {'import_academic_year': self.academic_year.pk}
        response = self.client.post(self.url, data, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/financings/financing_list.html')
        self.assertTemplateUsed(response, 'partnerships/financings/financing_import.html')

        response = self.submit_scv(self.filename_3)
        self.assertTemplateNotUsed(response, 'partnerships/financings/financing_list.html')
