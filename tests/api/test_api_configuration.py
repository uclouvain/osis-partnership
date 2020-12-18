from django.test import tag
from django.urls import reverse

from base.models.enums.entity_type import FACULTY, SECTOR
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory as BaseEducationGroupYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from partnership.models import PartnershipConfiguration, FundingSource
from partnership.tests import TestCase
from partnership.tests.factories import (
    PartnerFactory,
    PartnershipAgreementFactory, PartnershipFactory, PartnershipYearFactory,
    UCLManagementEntityFactory, FundingTypeFactory,
)
from reference.models.continent import Continent
from reference.tests.factories.country import CountryFactory
from reference.tests.factories.domain_isced import DomainIscedFactory


class ConfigurationApiViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):

        class EducationGroupYearFactory(BaseEducationGroupYearFactory):
            management_entity = None
            administration_entity = None
            enrollment_campus = None

        cls.url = reverse('partnership_api_v1:configuration')

        AcademicYearFactory.produce_in_future(quantity=2)
        current_academic_year = PartnershipConfiguration.get_configuration().get_current_academic_year_for_api()

        # Partnerships
        cls.supervisor_partnership = PersonFactory()
        cls.supervisor_management_entity = PersonFactory()

        partnership = PartnershipFactory(
            supervisor=cls.supervisor_partnership,
            years=[]
        )
        year = PartnershipYearFactory(
            partnership=partnership,
            academic_year=current_academic_year,
        )
        year.offers.add(EducationGroupYearFactory())
        education_field = DomainIscedFactory(title_en='foo', title_fr='bar')
        year.education_fields.add(education_field)
        PartnershipAgreementFactory(
            partnership=partnership,
            start_academic_year=current_academic_year,
            end_academic_year__year=current_academic_year.year + 1,
        )

        root = EntityWithVersionFactory()
        parent = EntityVersionFactory(acronym="SSH", entity_type=SECTOR, parent=root)
        partnership = PartnershipFactory(
            partner__contact_address=True,
            years__academic_year=current_academic_year,
            ucl_entity=EntityVersionFactory(
                acronym="FIAL", entity_type=FACULTY, parent=parent.entity,
            ).entity,
        )
        PartnershipAgreementFactory(
            partnership=partnership,
            start_academic_year=current_academic_year,
            end_academic_year__year=current_academic_year.year + 1,
        )
        UCLManagementEntityFactory(
            entity=partnership.ucl_entity,
            academic_responsible=cls.supervisor_management_entity
        )
        FundingSource.objects.all().delete()
        FundingTypeFactory()

        # Some noises
        cls.noisy_partner = PartnerFactory()
        cls.noisy_partnership = PartnershipFactory()

        # Continents
        continent = Continent.objects.create(code='AA', name='aaaaa')
        CountryFactory(continent=continent)
        CountryFactory(continent=continent)
        CountryFactory()

    @tag('perf')
    def test_num_queries(self):
        with self.assertNumQueriesLessThan(13):
            self.client.get(self.url)

    def test_continents(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('continents', data)
        self.assertEqual(len(data['continents']), 1)
        self.assertEqual(len(data['continents'][0]['countries']), 2)

    def test_partners(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('partners', data)
        self.assertEqual(len(data['partners']), 3)
        self.assertNotIn(
            self.noisy_partner.uuid,
            [p['value'] for p in data['partners']],
        )
        self.assertNotIn(
            self.noisy_partnership.partner.uuid,
            [p['value'] for p in data['partners']],
        )

    def test_ucl_universities(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('ucl_universities', data)
        self.assertEqual(len(data['ucl_universities']), 5)
        self.assertIn("SSH -", data['ucl_universities'][1]['label'])
        self.assertIn("SSH / FIAL -", data['ucl_universities'][2]['label'])

    def test_fundings(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('fundings', data)
        self.assertEqual(len(data['fundings']), 3)  # source, type and program
