from django.test import TestCase
from django.urls import reverse

from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.user import UserFactory
from partnership.tests.factories import PartnershipFactory, PartnerFactory, PartnerEntityFactory, PartnerTypeFactory, \
    PartnerTagFactory, PartnershipYearFactory, PartnershipTagFactory
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
        cls.partnership_university_offer.university_offers.add(cls.university_offer)
        # partner
        cls.partner = PartnerFactory()
        cls.partnership_partner = PartnershipFactory(partner=cls.partner)
        # partner_entity
        cls.partner_entity = PartnerEntityFactory()
        cls.partnership_partner_entity = PartnershipFactory(partner_entity=cls.partner_entity)
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
        country_continent = CountryFactory(continent=cls.continent)
        partner_continent = PartnerFactory(contact_address__country=country_continent)
        cls.partnership_continent = PartnershipFactory(partner=partner_continent)
        # partner_tags
        cls.partner_tag = PartnerTagFactory()
        partner_tag = PartnerFactory(tags=[cls.partner_tag])
        cls.partnership_partner_tags = PartnershipFactory(partner=partner_tag)
        # education_field
        cls.partnership_education_field = PartnershipFactory()
        PartnershipYearFactory(partnership=cls.partnership_education_field, education_field='1088')
        # education_level
        cls.partnership_education_level = PartnershipFactory()
        PartnershipYearFactory(partnership=cls.partnership_education_level, education_level='ISCED-9')
        # is_sms
        cls.partnership_is_sms = PartnershipFactory()
        PartnershipYearFactory(partnership=cls.partnership_is_sms, is_sms=True)
        # is_smp
        cls.partnership_is_smp = PartnershipFactory()
        PartnershipYearFactory(partnership=cls.partnership_is_smp, is_smp=True)
        # is_sta
        cls.partnership_is_sta = PartnershipFactory()
        PartnershipYearFactory(partnership=cls.partnership_is_sta, is_sta=True)
        # is_stt
        cls.partnership_is_stt = PartnershipFactory()
        PartnershipYearFactory(partnership=cls.partnership_is_stt, is_stt=True)
        # partnership_type
        cls.partnership_type = PartnershipFactory()
        PartnershipYearFactory(partnership=cls.partnership_type, partnership_type='codiplomation')
        # tags
        cls.tag = PartnershipTagFactory()
        cls.partnership_tag = PartnershipFactory(tags=[cls.tag])

        cls.user = UserFactory()
        cls.url = reverse('partnerships:list')

    def test_get_list_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partnerships_list.html')
        self.assertTemplateUsed(response, 'registration/login.html')

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
        response = self.client.get(self.url + '?university_offers=' + str(self.university_offer.pk))
        self.assertTemplateUsed(response, 'partnerships/partnerships_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_university_offer)

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
        response = self.client.get(self.url + '?education_field=1088')
        self.assertTemplateUsed(response, 'partnerships/partnerships_list.html')
        context = response.context_data
        self.assertEqual(len(context['partnerships']), 1)
        self.assertEqual(context['partnerships'][0], self.partnership_education_field)

    def test_filter_education_level(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?education_level=ISCED-9')
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
