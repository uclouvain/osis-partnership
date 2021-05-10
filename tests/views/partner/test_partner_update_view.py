from datetime import date
from unittest.mock import patch

from django.contrib.gis.geos import Point
from django.test import TestCase
from django.urls import reverse

from base.models.enums.organization_type import MAIN
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.user import UserFactory
from partnership.models import Partner
from partnership.tests.factories import (
    PartnerEntityFactory,
    PartnerFactory,
    PartnerTagFactory,
    PartnershipEntityManagerFactory,
)
from reference.tests.factories.country import CountryFactory


class PartnerUpdateViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # User creation
        cls.user = UserFactory()
        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(entity=entity_version.entity, person__user=cls.user_adri)
        cls.user_gf = UserFactory()
        entity_manager = PartnershipEntityManagerFactory(person__user=cls.user_gf)
        cls.user_other_gf = UserFactory()
        PartnershipEntityManagerFactory(person__user=cls.user_other_gf, entity=entity_manager.entity)

        # Partner creation
        cls.partner = PartnerFactory(organization__prefix='XABCDE')
        cls.partner_gf = PartnerFactory(author=cls.user_gf.person)
        # Misc
        cls.country = CountryFactory()

        cls.data = {
            'organization-name': 'test',
            'partner-is_valid': 'on',
            'organization-start_date': cls.partner.organization.start_date,
            'organization-end_date': '',
            'organization-type':  cls.partner.organization.type,
            'organization-code': 'test',
            'partner-pic_code': 'test',
            'partner-erasmus_code': 'test',
            'partner-is_nonprofit': 'True',
            'partner-is_public': 'True',
            'partner-use_egracons': 'on',
            'partner-comment': 'test',
            'partner-phone': 'test',
            'organization-website': 'http://localhost:8000',
            'partner-email': 'test@test.test',
            'partner-tags': [PartnerTagFactory().id],
            'contact_address-street': 'test',
            'contact_address-postal_code': 'test',
            'contact_address-city': 'test',
            'contact_address-country': cls.country.pk,
            'contact_address-location_0': 10,
            'contact_address-location_1': -12,
        }

        cls.url = reverse('partnerships:partners:update', kwargs={'pk': cls.partner.pk})

    def test_get_partner_as_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partners/partner_update.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_partner_as_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partners/partner_update.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_partner_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/partners/partner_update.html')

    def test_update_main_partner(self):
        self.client.force_login(self.user_adri)
        partner_main = PartnerFactory(organization__type=MAIN)
        url = reverse('partnerships:partners:update', kwargs={'pk': partner_main.pk})
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_other_partner_as_gf(self):
        self.client.force_login(self.user_gf)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partners/partner_update.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_own_partner_as_gf(self):
        self.client.force_login(self.user_gf)
        url = reverse('partnerships:partners:update', kwargs={'pk': self.partner_gf.pk})
        response = self.client.get(url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partners/partner_update.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_faculty_partner_as_gf(self):
        self.client.force_login(self.user_other_gf)
        url = reverse('partnerships:partners:update', kwargs={'pk': self.partner_gf.pk})
        response = self.client.get(url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partners/partner_update.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_post(self):
        self.client.force_login(self.user_adri)
        response = self.client.post(self.url, data=self.data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partners/partner_detail.html')
        self.partner.refresh_from_db()
        org = self.partner.organization
        self.assertEqual(org.prefix, 'XABCDE')
        self.assertEqual(org.entity_set.count(), 1)
        entity = org.entity_set.first()
        self.assertEqual(entity.most_recent_acronym, 'XABCDE')

    def test_post_with_child_entity(self):
        # Create a child partner entity on the same organization
        PartnerEntityFactory(partner=self.partner)

        self.client.force_login(self.user_adri)
        response = self.client.post(self.url, data=self.data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partners/partner_detail.html')

    def test_repost_and_not_ies(self):
        self.client.force_login(self.user_adri)
        data = self.data.copy()
        data['partner-pic_code'] = ''
        data['partner-contact_type'] = Partner.CONTACT_TYPE_CHOICES[-1][0]

        # City and country are mandatory if not ies or pic_code empty, but provided
        response = self.client.post(self.url, data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partners/partner_detail.html')

        # If we repost it with same data, should not fail
        response = self.client.post(self.url, data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partners/partner_detail.html')


class PartnerUpdateVersionsViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # User creation
        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(entity=entity_version.entity, person__user=cls.user_adri)

    def setUp(self):
        self.country = CountryFactory()

        # Partner creation
        self.partner = PartnerFactory(
            is_valid=False,
            erasmus_code=None,
            is_nonprofit=None,
            is_public=None,
            email=None,
            phone=None,
            contact_address__city='test',
            contact_address__country_id=self.country.pk,
            contact_address__location=Point(-12, 10),
        )

        # For the start_date for the test
        self.start_date = self.partner.organization.start_date
        self.entity = self.partner.organization.entity_set.first()
        version = self.entity.get_latest_entity_version()
        version.start_date = date(2007, 7, 7)
        version.save()
        address = self.partner.contact_address
        self.assertEqual(self.entity.entityversion_set.count(), 1)
        self.start_date = self.partner.organization.start_date
        self.data = {
            'organization-name': self.partner.organization.name,
            'organization-start_date': self.start_date,
            'organization-type':  self.partner.organization.type,
            'organization-end_date': '',
            'partner-pic_code': self.partner.pic_code,
            'organization-website': self.partner.organization.website,
            'contact_address-city': 'test',
            'contact_address-country': self.country.pk,
            'contact_address-street_number': address.street_number,
            'contact_address-street': address.street,
            'contact_address-state': address.state,
            'contact_address-postal_code': address.postal_code,
            'contact_address-location_0': 10.0,
            'contact_address-location_1': -12.0,
        }

        self.url = reverse('partnerships:partners:update', kwargs={'pk': self.partner.pk})
        self.client.force_login(self.user_adri)
        self.assertEqual(self.entity.entityversion_set.count(), 1)

    def test_post_unchanged(self):
        response = self.client.post(self.url, data=self.data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partners/partner_detail.html')
        self.assertEqual(self.entity.entityversion_set.count(), 1)

    def test_newer_start_date_truncates(self):
        """New start date is after the original start, truncate first version"""
        data = self.data.copy()
        data['organization-start_date'] = "01/01/2010"
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partners/partner_detail.html')
        self.assertEqual(self.entity.entityversion_set.count(), 2)
        self.assertEqual(self.partner.organization.start_date, date(2010, 1, 1))
        self.assertEqual(self.partner.organization.end_date, None)

    def test_older_start_date_extends(self):
        """New start date is before the original start, extends first version"""
        data = self.data.copy()
        data['organization-start_date'] = "01/01/2005"
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partners/partner_detail.html')
        self.assertEqual(self.entity.entityversion_set.count(), 2)
        self.assertEqual(self.partner.organization.start_date, date(2005, 1, 1))
        self.assertEqual(self.partner.organization.end_date, None)

    def test_post_wrong_end_date(self):
        """Form should be invalid with non consecutive dates"""
        data = self.data.copy()
        data['organization-end_date'] = "01/01/2003"
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partners/partner_detail.html')

    def test_change_info(self):
        """The old version version should be updated if changed"""
        data = self.data.copy()
        data['organization-name'] = "Tic"
        with patch('partnership.views.partner.mixins.date') as mock_date:
            mock_date.today.return_value = date(2015, 2, 2)
            response = self.client.post(self.url, data=data, follow=True)

        self.assertTemplateUsed(response, 'partnerships/partners/partner_detail.html')
        qs = self.entity.entityversion_set.order_by('start_date')
        self.assertEqual(qs.first().end_date, date(2015, 2, 1))
        self.assertEqual(qs.last().start_date, date(2015, 2, 2))

    def test_change_info_twice_in_the_same_day(self):
        """The same version should be used if change twice within the day"""
        data = self.data.copy()
        data['organization-name'] = "Tic"
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partners/partner_detail.html')

        data['organization-name'] = "Tac"
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partners/partner_detail.html')
        self.assertEqual(self.entity.entityversion_set.count(), 2)

    def test_changing_start_date_with_two_versions(self):
        # 2 entity versions (07/07/2007 -> 01/02/2015 | 02/02/2015 -> None)
        data = self.data.copy()
        data['organization-name'] = "Test2"

        with patch('partnership.views.partner.mixins.date') as mock_date:
            mock_date.today.return_value = date(2015, 2, 2)
            response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partners/partner_detail.html')
        self.assertEqual(self.entity.entityversion_set.count(), 2)
        self.assertEqual(self.partner.organization.start_date, date(2007, 7, 7))
        self.assertEqual(self.partner.organization.end_date, None)

        # Before the already set date of the 1st version
        data['organization-start_date'] = "01/01/2005"
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partners/partner_detail.html')
        self.assertEqual(self.entity.entityversion_set.count(), 3)
        self.assertEqual(self.partner.organization.start_date, date(2005, 1, 1))
        self.assertEqual(self.partner.organization.end_date, None)

    def test_newer_end_date_truncates(self):
        """New end date is after the original start, truncate end version"""
        data = self.data.copy()
        data['organization-end_date'] = "01/01/2025"
        with patch('partnership.views.partner.mixins.date') as mock_date:
            mock_date.today.return_value = date(2020, 1, 1)
            response = self.client.post(self.url, data=data, follow=True)
            self.assertTemplateUsed(response, 'partnerships/partners/partner_detail.html')
            self.assertEqual(self.entity.entityversion_set.count(), 2)
            self.assertEqual(self.partner.organization.end_date, date(2025, 1, 1))

            data['organization-end_date'] = "01/01/2023"
            response = self.client.post(self.url, data=data, follow=True)
            self.assertTemplateUsed(response, 'partnerships/partners/partner_detail.html')
            self.assertEqual(self.entity.entityversion_set.count(), 2)
            self.assertEqual(self.partner.organization.end_date, date(2023, 1, 1))

    def test_end_date_before_today_truncates(self):
        """New end date is before today (and the original end_date), truncates first version"""
        data = self.data.copy()
        data['organization-end_date'] = "01/01/2030"
        with patch('partnership.views.partner.mixins.date') as mock_date:
            mock_date.today.return_value = date(2031, 1, 1)
            response = self.client.post(self.url, data=data, follow=True)
            self.assertTemplateUsed(response, 'partnerships/partners/partner_detail.html')
            self.assertEqual(self.entity.entityversion_set.count(), 1)
            self.assertEqual(self.partner.organization.end_date, date(2030, 1, 1))

            data['organization-end_date'] = "01/01/2029"
            response = self.client.post(self.url, data=data, follow=True)
            self.assertTemplateUsed(response, 'partnerships/partners/partner_detail.html')
            self.assertEqual(self.entity.entityversion_set.count(), 1)
            self.assertEqual(self.partner.organization.end_date, date(2029, 1, 1))

    def test_older_end_date_extends(self):
        """New end date is after the original end, extends first version"""
        data = self.data.copy()
        data['organization-end_date'] = "01/01/2023"
        with patch('partnership.views.partner.mixins.date') as mock_date:
            mock_date.today.return_value = date(2020, 1, 1)
            response = self.client.post(self.url, data=data, follow=True)
            self.assertTemplateUsed(response, 'partnerships/partners/partner_detail.html')
            self.assertEqual(self.entity.entityversion_set.count(), 2)
            self.assertEqual(self.partner.organization.end_date, date(2023, 1, 1))

            data['organization-end_date'] = "01/01/2025"
            response = self.client.post(self.url, data=data, follow=True)
            self.assertTemplateUsed(response, 'partnerships/partners/partner_detail.html')
            self.assertEqual(self.entity.entityversion_set.count(), 2)
            self.assertEqual(self.partner.organization.end_date, date(2025, 1, 1))
