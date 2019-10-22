from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from base.models.academic_year import AcademicYear
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.user import UserFactory
from osis_common.document.xls_build import CONTENT_TYPE_XLS
from partnership.models import PartnershipAgreement
from partnership.tests.factories import (
    PartnerEntityFactory, PartnerFactory,
    PartnershipAgreementFactory,
    PartnershipFactory,
    PartnershipTagFactory,
    PartnershipYearEducationFieldFactory,
    PartnershipYearEducationLevelFactory,
    PartnershipYearFactory,
    PartnerTagFactory, PartnerTypeFactory
)
from reference.models.continent import Continent
from reference.tests.factories.country import CountryFactory


class PartnershipsListViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        for i in range(15):
            PartnershipFactory()
        cls.partnership_first_name = PartnershipFactory(partner__name='aaaaaa')
        # ucl_university
        cls.ucl_university = EntityFactory()
        cls.partnership_ucl_university = PartnershipFactory(ucl_university=cls.ucl_university)
        # ucl_university_labo
        cls.ucl_university_labo = EntityFactory()
        cls.partnership_ucl_university_labo = PartnershipFactory(ucl_university_labo=cls.ucl_university_labo)
        # university_offer
        cls.university_offer = EducationGroupYearFactory()
        cls.partnership_university_offer = PartnershipFactory()
        partnership_year = PartnershipYearFactory(partnership=cls.partnership_university_offer, academic_year__year=2101)
        partnership_year.offers.add(cls.university_offer)
        # partner
        cls.partner = PartnerFactory()
        cls.partnership_partner = PartnershipFactory(partner=cls.partner)
        # partner_entity
        cls.partner_entity = PartnerEntityFactory()
        cls.partnership_partner_entity = PartnershipFactory(partner_entity=cls.partner_entity)
        # use_egracons
        cls.partnership_use_egracons = PartnershipFactory(partner__use_egracons=True)
        # partner_type
        cls.partner_type = PartnerTypeFactory()
        cls.partnership_partner_type = PartnershipFactory(partner__partner_type=cls.partner_type)
        # city
        cls.partner_city = PartnerFactory(contact_address__city='foobar')
        cls.partnership_city = PartnershipFactory(partner=cls.partner_city)
        # country
        cls.country = CountryFactory()
        partner_country = PartnerFactory(contact_address__country=cls.country)
        cls.partnership_country = PartnershipFactory(partner=partner_country)
        # continent
        cls.continent = Continent.objects.create(code='fo', name='foo')
        country_continent = CountryFactory()
        country_continent.continent = cls.continent
        country_continent.save()
        partner_continent = PartnerFactory(contact_address__country=country_continent)
        cls.partnership_continent = PartnershipFactory(partner=partner_continent)
        # partner_tags
        cls.partner_tag = PartnerTagFactory()
        partner_tag = PartnerFactory(tags=[cls.partner_tag])
        cls.partnership_partner_tags = PartnershipFactory(partner=partner_tag)
        # education_field
        cls.education_field = PartnershipYearEducationFieldFactory()
        partnership_year = PartnershipYearFactory(academic_year__year=2120)
        partnership_year.education_fields.add(cls.education_field)
        cls.partnership_education_field = PartnershipFactory(years=[partnership_year])
        partnership_year.offers.add(EducationGroupYearFactory())
        # education_level
        cls.education_level = PartnershipYearEducationLevelFactory()
        partnership_year = PartnershipYearFactory(academic_year__year=2120)
        partnership_year.education_levels.add(cls.education_level)
        cls.partnership_education_level = PartnershipFactory(years=[partnership_year])
        # is_sms
        cls.partnership_is_sms = PartnershipFactory()
        PartnershipYearFactory(partnership=cls.partnership_is_sms, is_sms=True, academic_year__year=2150)
        # is_smp
        cls.partnership_is_smp = PartnershipFactory()
        PartnershipYearFactory(partnership=cls.partnership_is_smp, is_smp=True, academic_year__year=2151)
        # is_sta
        cls.partnership_is_sta = PartnershipFactory()
        PartnershipYearFactory(partnership=cls.partnership_is_sta, is_sta=True, academic_year__year=2152)
        # is_stt
        cls.partnership_is_stt = PartnershipFactory()
        PartnershipYearFactory(partnership=cls.partnership_is_stt, is_stt=True, academic_year__year=2153)
        # partnership_type
        cls.partnership_type = PartnershipFactory()
        PartnershipYearFactory(
            partnership=cls.partnership_type,
            partnership_type='codiplomation',
            academic_year__year=2154,
        )
        # tags
        cls.tag = PartnershipTagFactory()
        cls.partnership_tag = PartnershipFactory(tags=[cls.tag])
        # comment
        cls.partnership_comment = PartnershipFactory(comment='foobar')
        # partnership_in
        cls.partnership_partnership_in = PartnershipFactory()
        PartnershipAgreementFactory(
            partnership=cls.partnership_partnership_in,
            start_academic_year__year=2115,
            end_academic_year__year=2116,
        )
        # partnership_ending_in
        cls.partnership_partnership_ending_in = PartnershipFactory()
        PartnershipAgreementFactory(
            partnership=cls.partnership_partnership_ending_in,
            start_academic_year__year=2108,
            end_academic_year__year=2109,
        )
        # partnership_valid_in
        cls.partnership_partnership_valid_in = PartnershipFactory()
        PartnershipAgreementFactory(
            partnership=cls.partnership_partnership_valid_in,
            status=PartnershipAgreement.STATUS_VALIDATED,
            start_academic_year__year=2117,
            end_academic_year__year=2118,
        )
        # partnership_ending_in
        cls.partnership_partnership_not_valid_in = PartnershipFactory()
        PartnershipAgreementFactory(
            partnership=cls.partnership_partnership_not_valid_in,
            start_academic_year__year=2119,
            end_academic_year__year=2120,
        )
        # partnership_no_agreement_in
        cls.partnership_partnership_no_agreement_in = PartnershipFactory(years=[])
        PartnershipYearFactory(
            partnership=cls.partnership_partnership_no_agreement_in,
            academic_year__year=2180,
        )
        # All filters
        country = CountryFactory(continent=Continent.objects.create(code='ba', name='bar'))
        cls.partnership_all_filters = PartnershipFactory(
            ucl_university_labo=EntityFactory(),
            partner__contact_address__city='all_filters',
            partner__contact_address__country=country,
            comment='all_filters',
        )
        cls.partnership_all_filters.partner.tags.add(PartnerTagFactory())
        partnership_year = PartnershipYearFactory(
            partnership=cls.partnership_all_filters,
            is_sms=False,
            is_smp=False,
            is_sta=False,
            is_stt=False,
            partnership_type='autre',
            academic_year__year=2160,
        )
        partnership_year.offers.add(EducationGroupYearFactory())
        cls.all_education_field = PartnershipYearEducationFieldFactory()
        partnership_year.education_fields.add(cls.all_education_field)
        cls.all_education_level = PartnershipYearEducationLevelFactory()
        partnership_year.education_levels.add(cls.all_education_level)
        cls.partnership_all_filters.tags.add(PartnershipTagFactory())
        PartnershipAgreementFactory(
            partnership=cls.partnership_all_filters,
            start_academic_year__year=2125,
            end_academic_year__year=2127,
        )
        PartnershipAgreementFactory(
            partnership=cls.partnership_all_filters,
            status=PartnershipAgreement.STATUS_VALIDATED,
            start_academic_year__year=2127,
            end_academic_year__year=2129,
        )
        AcademicYearFactory(year=2126)

        cls.user = UserFactory()
        cls.user.user_permissions.add(Permission.objects.get(name='can_access_partnerships'))
        cls.url = reverse('partnerships:list')

    def test_get_list_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partnerships_list.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_list_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnerships_list.html')

    def test_get_list_pagination(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?page=1', follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnerships_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 20)

    def test_get_list_ordering(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?ordering=partner__name', follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnerships_list.html')
        context = response.context_data
        self.assertEqual(context['partnerships'][0], self.partnership_first_name)

    def test_get_list_ordering_country(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?ordering=country', follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnerships_list.html')

    def test_filter_ucl_university(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?ucl_university=' + str(self.ucl_university.pk))
        self.assertTemplateUsed(response, 'partnerships/partnerships_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_ucl_university)

    def test_filter_ucl_university_labo(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?ucl_university_labo=' + str(self.ucl_university_labo.pk))
        self.assertTemplateUsed(response, 'partnerships/partnerships_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_ucl_university_labo)

    def test_filter_university_offers(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?university_offer=' + str(self.university_offer.pk))
        self.assertTemplateUsed(response, 'partnerships/partnerships_list.html')
        context = response.context_data
        self.assertEqual(context['paginator'].count, 43)  # Include partnerships with offers at None

    def test_filter_partner(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?partner=' + str(self.partner.pk))
        self.assertTemplateUsed(response, 'partnerships/partnerships_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_partner)

    def test_filter_partner_entity(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?partner_entity=' + str(self.partner_entity.pk))
        self.assertTemplateUsed(response, 'partnerships/partnerships_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_partner_entity)
        
    def test_filter_use_egracons(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?use_egracons=True')
        self.assertTemplateUsed(response, 'partnerships/partnerships_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_use_egracons)

    def test_filter_partner_type(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?partner_type=' + str(self.partner_type.pk))
        self.assertTemplateUsed(response, 'partnerships/partnerships_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_partner_type)

    def test_filter_city(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?city=foobar')
        self.assertTemplateUsed(response, 'partnerships/partnerships_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_city)

    def test_filter_country(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?country=' + str(self.country.pk))
        self.assertTemplateUsed(response, 'partnerships/partnerships_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_country)

    def test_filter_continent(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?continent=' + str(self.continent.pk))
        self.assertTemplateUsed(response, 'partnerships/partnerships_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_continent)

    def test_filter_partner_tags(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?partner_tags=' + str(self.partner_tag.pk))
        self.assertTemplateUsed(response, 'partnerships/partnerships_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_partner_tags)

    def test_filter_education_field(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?education_field=' + str(self.education_field.pk))
        self.assertTemplateUsed(response, 'partnerships/partnerships_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_education_field)

    def test_filter_education_level(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?education_level=' + str(self.education_level.pk))
        self.assertTemplateUsed(response, 'partnerships/partnerships_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_education_level)

    def test_filter_is_sms(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?is_sms=True')
        self.assertTemplateUsed(response, 'partnerships/partnerships_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_is_sms)

    def test_filter_is_smp(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?is_smp=True')
        self.assertTemplateUsed(response, 'partnerships/partnerships_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_is_smp)

    def test_filter_is_sta(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?is_sta=True')
        self.assertTemplateUsed(response, 'partnerships/partnerships_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_is_sta)

    def test_filter_is_stt(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?is_stt=True')
        self.assertTemplateUsed(response, 'partnerships/partnerships_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_is_stt)

    def test_filter_partnership_type(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?partnership_type=codiplomation')
        self.assertTemplateUsed(response, 'partnerships/partnerships_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_type)

    def test_filter_tags(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?tags=' + str(self.tag.pk))
        self.assertTemplateUsed(response, 'partnerships/partnerships_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_tag)

    def test_filter_comment(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?comment=foo')
        self.assertTemplateUsed(response, 'partnerships/partnerships_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_comment)

    def test_filter_partnership_in(self):
        self.client.force_login(self.user)
        academic_year = self.partnership_partnership_in.agreements.first().start_academic_year
        response = self.client.get(self.url + '?partnership_in=' + str(academic_year.pk))
        self.assertTemplateUsed(response, 'partnerships/partnerships_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_partnership_in)

    def test_filter_partnership_ending_in(self):
        self.client.force_login(self.user)
        academic_year = self.partnership_partnership_ending_in.agreements.first().end_academic_year
        response = self.client.get(self.url + '?partnership_ending_in=' + str(academic_year.pk))
        self.assertTemplateUsed(response, 'partnerships/partnerships_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_partnership_ending_in)

    def test_filter_partnership_valid_in(self):
        self.client.force_login(self.user)
        academic_year = self.partnership_partnership_valid_in.agreements.first().start_academic_year
        response = self.client.get(self.url + '?partnership_valid_in=' + str(academic_year.pk))
        self.assertTemplateUsed(response, 'partnerships/partnerships_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_partnership_valid_in)

    def test_filter_partnership_not_valid_in(self):
        self.client.force_login(self.user)
        academic_year = self.partnership_partnership_not_valid_in.agreements.first().start_academic_year
        response = self.client.get(self.url + '?partnership_not_valid_in=' + str(academic_year.pk))
        self.assertTemplateUsed(response, 'partnerships/partnerships_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_partnership_not_valid_in)

    def test_filter_partnership_no_agreements_in(self):
        self.client.force_login(self.user)
        academic_year = self.partnership_partnership_no_agreement_in.years.first().academic_year
        response = self.client.get(self.url + '?partnership_with_no_agreements_in=' + str(academic_year.pk))
        self.assertTemplateUsed(response, 'partnerships/partnerships_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_partnership_no_agreement_in)

    def test_all_filters(self):
        self.client.force_login(self.user)
        query = '&'.join(['{0}={1}'.format(key, value) for key, value in {
            'ucl_university': str(self.partnership_all_filters.ucl_university.pk),
            'ucl_university_labo': str(self.partnership_all_filters.ucl_university_labo.pk),
            'university_offers': str(self.partnership_all_filters.years.filter(offers__isnull=False).first().offers.first().pk),
            'partner': str(self.partnership_all_filters.partner.pk),
            'use_egracons': 'False',
            'partner_entity': str(self.partnership_all_filters.partner_entity.pk),
            'city': 'all_filters',
            'country': str(self.partnership_all_filters.partner.contact_address.country.pk),
            'continent': str(self.partnership_all_filters.partner.contact_address.country.continent.pk),
            'partner_tags': str(self.partnership_all_filters.partner.tags.first().pk),
            'education_field': str(self.all_education_field.pk),
            'education_level': str(self.all_education_level.pk),
            'is_sms': 'False',
            'is_smp': 'False',
            'is_sta': 'False',
            'is_stt': 'False',
            'partnership_type': 'autre',
            'tags': str(self.partnership_all_filters.tags.first().pk),
            'comment': 'all_filters',
            'partnership_in': str(AcademicYear.objects.get(year=2125).pk),
            'partnership_ending_in': str(AcademicYear.objects.get(year=2129).pk),
            'partnership_valid_in': str(AcademicYear.objects.get(year=2127).pk),
            'partnership_not_valid_in': str(AcademicYear.objects.get(year=2126).pk),
        }.items()])
        response = self.client.get(self.url + '?' + query)
        self.assertTemplateUsed(response, 'partnerships/partnerships_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_all_filters)

    def test_export_all(self):
        self.client.force_login(self.user)
        url = reverse('partnerships:export')
        response = self.client.get(url)
        self.assertTemplateNotUsed(response, 'partnerships/partnerships_list.html')
        self.assertEqual(response['Content-Type'], CONTENT_TYPE_XLS)
