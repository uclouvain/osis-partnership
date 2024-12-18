from django.shortcuts import resolve_url
from django.test import TestCase

from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.user import UserFactory
from partnership.models import ContactTitle, ContactType, PartnerEntity
from partnership.tests.factories import (
    PartnerEntityFactory, PartnerFactory,
    PartnershipEntityManagerFactory,
)
from reference.tests.factories.country import CountryFactory


class PartnerEntityCreateViewTest(TestCase):
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
        cls.partner = PartnerFactory(
            organization__prefix='XABCDE',
        )
        cls.partner_gf = PartnerFactory(author=cls.user_gf.person)
        # Misc
        cls.contact_type = ContactType.objects.create(value='foobar')
        cls.country = CountryFactory()
        cls.url = resolve_url('partnerships:partners:entities:create', partner_pk=cls.partner.pk)

    def test_get_view_as_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partners/entities/partner_entity_create.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_view_as_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partners/entities/partner_entity_create.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_view_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/partners/entities/partner_entity_create.html')

    def test_get_as_gf(self):
        self.client.force_login(self.user_gf)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/partners/entities/partner_entity_create.html')

    def test_post_invalid(self):
        self.client.force_login(self.user_adri)
        data = {'name': ''}  # At least the name is required
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partners/partner_detail.html')

    def test_post(self):
        self.client.force_login(self.user_adri)
        data = {
            'name': 'test',
            'comment': 'test',
            'address-street_number': 'test',
            'address-street': 'test',
            'address-postal_code': '13245',
            'address-state': 'state',
            'address-city': 'test',
            'address-location_0': 30,
            'address-location_1': 15,
            'address-country': self.country.pk,
            'contact_in-type': self.contact_type.pk,
            'contact_in-title': ContactTitle.MISTER.name,
            'contact_in-last_name': 'test',
            'contact_in-first_name': 'test',
            'contact_in-function': 'test',
            'contact_in-phone': 'test',
            'contact_in-mobile_phone': 'test',
            'contact_in-fax': 'test',
            'contact_in-email': 'test@test.test',
            'contact_out-type': self.contact_type.pk,
            'contact_out-title': ContactTitle.MISTER.name,
            'contact_out-last_name': 'test',
            'contact_out-first_name': 'test',
            'contact_out-function': 'test',
            'contact_out-phone': 'test',
            'contact_out-mobile_phone': 'test',
            'contact_out-fax': 'test',
            'contact_out-email': 'test@test.test',
            'parent': '',
        }
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partners/partner_detail.html')
        partner_entity = PartnerEntity.objects.last()
        last_version = partner_entity.entity.entityversion_set.last()
        self.assertEqual(last_version.acronym, 'XABCDEA')


class PartnerEntityUpdateViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # User creation
        cls.user = UserFactory()
        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(entity=entity_version.entity, person__user=cls.user_adri, with_child=False)
        cls.user_gf = UserFactory()
        entity_manager = PartnershipEntityManagerFactory(person__user=cls.user_gf, with_child=False)
        cls.user_other_gf = UserFactory()
        PartnershipEntityManagerFactory(person__user=cls.user_other_gf, entity=entity_manager.entity, with_child=False)

        # Partner creation
        cls.partner = PartnerFactory(author=PersonFactory())
        cls.parent_entity = PartnerEntityFactory(
            partner=cls.partner,
            author=cls.partner.author,
        )
        cls.partner_entity = PartnerEntityFactory(
            partner=cls.partner,
            author=cls.partner.author,
            entity__version__parent=cls.parent_entity.entity,
        )

        cls.partner_gf = PartnerFactory(author=cls.user_gf.person)
        cls.partner_entity_gf = PartnerEntityFactory(
            partner=cls.partner_gf,
            author=cls.partner_gf.author,
        )
        # Misc
        cls.contact_type = ContactType.objects.create(value='foobar')
        cls.country = CountryFactory()
        cls.url = resolve_url(
            'partnerships:partners:entities:update',
            partner_pk=cls.partner.pk,
            pk=cls.partner_entity.pk,
        )
        cls.gf_url = resolve_url(
            'partnerships:partners:entities:update',
            partner_pk=cls.partner_gf.pk,
            pk=cls.partner_entity_gf.pk,
        )

        cls.data = {
            'name': 'test',
            'comment': 'test',
            'address-street_number': 'test',
            'address-street': 'test',
            'address-postal_code': '13245',
            'address-state': 'state',
            'address-city': 'test',
            'address-country': cls.country.pk,
            'address-location_0': 30,
            'address-location_1': 15,
            'contact_in-type': cls.contact_type.pk,
            'contact_in-title': ContactTitle.MISTER.name,
            'contact_in-last_name': 'test',
            'contact_in-first_name': 'test',
            'contact_in-function': 'test',
            'contact_in-phone': 'test',
            'contact_in-mobile_phone': 'test',
            'contact_in-fax': 'test',
            'contact_in-email': 'test@test.test',
            'contact_out-type': cls.contact_type.pk,
            'contact_out-title': ContactTitle.MISTER.name,
            'contact_out-last_name': 'test',
            'contact_out-first_name': 'test',
            'contact_out-function': 'test',
            'contact_out-phone': 'test',
            'contact_out-mobile_phone': 'test',
            'contact_out-fax': 'test',
            'contact_out-email': 'test@test.test',
            'parent': cls.parent_entity.entity_id,
        }

    def test_get_view_as_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partners/entities/partner_entity_update.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_view_as_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partners/entities/partner_entity_update.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_view_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/partners/entities/partner_entity_update.html')

    def test_get_other_partner_as_gf(self):
        self.client.force_login(self.user_gf)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partners/entities/partner_entity_update.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_own_partner_as_gf(self):
        self.client.force_login(self.user_gf)
        response = self.client.get(self.gf_url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partners/entities/partner_entity_update.html')

    def test_get_faculty_partner_as_gf(self):
        self.client.force_login(self.user_other_gf)
        response = self.client.get(self.gf_url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partners/entities/partner_entity_update.html')

    def test_absolute_url(self):
        partner_url = resolve_url('partnerships:partners:detail', pk=self.partner.pk)
        self.assertEqual(
            self.partner_entity.get_absolute_url(),
            partner_url + '#partner-entity-' + str(self.partner_entity.pk)
        )

    def test_post(self):
        self.client.force_login(self.user_adri)
        current_entity = self.partner_entity.entity
        acronym = current_entity.entityversion_set.last().acronym
        self.assertEqual(self.partner_entity.parent_entity, self.parent_entity)
        self.assertEqual(current_entity.entityversion_set.count(), 1)

        response = self.client.post(self.url, data=self.data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partners/partner_detail.html')
        # Should find postal code of last version
        self.assertContains(response, '13245')
        # Should have two versions
        self.assertEqual(current_entity.entityversion_set.count(), 2)
        # Should still be parent
        self.partner_entity.refresh_from_db()
        self.assertEqual(self.partner_entity.parent_entity, self.parent_entity)

        last_version = self.partner_entity.entity.entityversion_set.last()
        self.assertEqual(last_version.acronym, acronym)

        # If we set the same data
        response = self.client.post(self.url, data=self.data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partners/partner_detail.html')
        # Should still have only two versions
        self.assertEqual(current_entity.entityversion_set.count(), 2)


class PartnerEntityDeleteViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # User creation
        cls.user = UserFactory()
        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(entity=entity_version.entity, person__user=cls.user_adri, with_child=False)
        cls.user_gf = UserFactory()
        entity_manager = PartnershipEntityManagerFactory(person__user=cls.user_gf, with_child=False)
        cls.user_other_gf = UserFactory()
        PartnershipEntityManagerFactory(person__user=cls.user_other_gf, entity=entity_manager.entity, with_child=False)

        # Partner creation
        cls.partner = PartnerFactory(author=PersonFactory())
        cls.partner_entity = PartnerEntityFactory(
            partner=cls.partner,
            author=cls.partner.author,
        )

        cls.partner_gf = PartnerFactory(author=cls.user_gf.person)
        cls.partner_entity_gf = PartnerEntityFactory(
            partner=cls.partner_gf,
            author=cls.partner_gf.author,
        )
        # Misc
        cls.contact_type = ContactType.objects.create(value='foobar')
        cls.country = CountryFactory()
        cls.url = resolve_url(
            'partnerships:partners:entities:delete',
            partner_pk=cls.partner.pk,
            pk=cls.partner_entity.pk,
        )
        cls.gf_url = resolve_url(
            'partnerships:partners:entities:delete',
            partner_pk=cls.partner_gf.pk,
            pk=cls.partner_entity_gf.pk,
        )

    def test_get_view_as_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partners/entities/partner_entity_delete.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_view_as_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partners/entities/partner_entity_delete.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_view_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/partners/entities/partner_entity_delete.html')

    def test_get_other_partner_as_gf(self):
        self.client.force_login(self.user_gf)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partners/entities/partner_entity_delete.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_own_partner_as_gf(self):
        self.client.force_login(self.user_gf)
        response = self.client.get(self.gf_url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partners/entities/partner_entity_delete.html')

    def test_get_faculty_partner_as_gf(self):
        self.client.force_login(self.user_other_gf)
        response = self.client.get(self.gf_url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partners/entities/partner_entity_delete.html')

    def test_post(self):
        self.client.force_login(self.user_adri)
        response = self.client.post(self.url, data={}, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partners/partner_detail.html')

    def test_get_as_ajax(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url, data={}, headers={"x-requested-with": 'XMLHttpRequest'})
        self.assertTemplateUsed(response, 'partnerships/partners/entities/includes/partner_entity_delete.html')
        self.assertTemplateNotUsed(response, 'partnerships/partners/entities/partner_entity_delete.html')

    def test_post_as_ajax(self):
        self.client.force_login(self.user_adri)
        response = self.client.post(self.url, data={}, headers={"x-requested-with": 'XMLHttpRequest'}, follow=True)
        self.assertEqual(response.status_code, 200)
