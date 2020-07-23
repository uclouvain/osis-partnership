from django.shortcuts import resolve_url
from django.test import TestCase

from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.user import UserFactory
from partnership.models import ContactTitle, ContactType
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
        cls.partner = PartnerFactory()
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
            'address_street_number': 'test',
            'address_street': 'test',
            'address_postal_code': '13245',
            'address_state': 'state',
            'address_city': 'test',
            'address_country': self.country.pk,
            'contact_in_type': self.contact_type.pk,
            'contact_in_title': ContactTitle.MISTER.name,
            'contact_in_last_name': 'test',
            'contact_in_first_name': 'test',
            'contact_in_function': 'test',
            'contact_in_phone': 'test',
            'contact_in_mobile_phone': 'test',
            'contact_in_fax': 'test',
            'contact_in_email': 'test@test.test',
            'contact_out_type': self.contact_type.pk,
            'contact_out_title': ContactTitle.MISTER.name,
            'contact_out_last_name': 'test',
            'contact_out_first_name': 'test',
            'contact_out_function': 'test',
            'contact_out_phone': 'test',
            'contact_out_mobile_phone': 'test',
            'contact_out_fax': 'test',
            'contact_out_email': 'test@test.test',
            'parent': '',
        }
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partners/partner_detail.html')


class PartnerEntityUpdateViewTest(TestCase):
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
        cls.partner = PartnerFactory(author=PersonFactory())
        cls.parent_entity = PartnerEntityFactory(
            partner=cls.partner,
            author=cls.partner.author,
        )
        cls.partner_entity = PartnerEntityFactory(
            partner=cls.partner,
            author=cls.partner.author,
            entity_version__parent=cls.parent_entity.entity_version.entity,
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
        data = {
            'name': 'test',
            'comment': 'test',
            'address_street_number': 'test',
            'address_street': 'test',
            'address_postal_code': '13245',
            'address_state': 'state',
            'address_city': 'test',
            'address_country': self.country.pk,
            'contact_in_type': self.contact_type.pk,
            'contact_in_title': ContactTitle.MISTER.name,
            'contact_in_last_name': 'test',
            'contact_in_first_name': 'test',
            'contact_in_function': 'test',
            'contact_in_phone': 'test',
            'contact_in_mobile_phone': 'test',
            'contact_in_fax': 'test',
            'contact_in_email': 'test@test.test',
            'contact_out_type': self.contact_type.pk,
            'contact_out_title': ContactTitle.MISTER.name,
            'contact_out_last_name': 'test',
            'contact_out_first_name': 'test',
            'contact_out_function': 'test',
            'contact_out_phone': 'test',
            'contact_out_mobile_phone': 'test',
            'contact_out_fax': 'test',
            'contact_out_email': 'test@test.test',
            'parent': self.parent_entity.entity_version.entity_id,
        }
        current_entity = self.partner_entity.entity_version.entity
        self.assertEqual(self.partner_entity.parent_entity, self.parent_entity)
        self.assertEqual(current_entity.entityversion_set.count(), 1)

        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partners/partner_detail.html')
        # Should have two versions
        self.assertEqual(current_entity.entityversion_set.count(), 2)
        # Should still be parent
        self.partner_entity.refresh_from_db()
        self.assertEqual(self.partner_entity.parent_entity, self.parent_entity)


class PartnerEntityDeleteViewTest(TestCase):
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
        response = self.client.get(self.url, data={}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertTemplateUsed(response, 'partnerships/partners/entities/includes/partner_entity_delete.html')
        self.assertTemplateNotUsed(response, 'partnerships/partners/entities/partner_entity_delete.html')

    def test_post_as_ajax(self):
        self.client.force_login(self.user_adri)
        response = self.client.post(self.url, data={}, HTTP_X_REQUESTED_WITH='XMLHttpRequest', follow=True)
        self.assertEqual(response.status_code, 200)
