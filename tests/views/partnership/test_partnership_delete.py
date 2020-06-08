from django.contrib.auth.models import Permission
from django.shortcuts import resolve_url
from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from base.models.enums.entity_type import FACULTY, SECTOR
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.user import UserFactory
from partnership.tests.factories import (
    PartnershipAgreementFactory, PartnershipEntityManagerFactory,
    PartnershipFactory,
    UCLManagementEntityFactory,
)


class PartnershipDeleteViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.template_name = 'partnerships/partnership/partnership_confirm_delete.html'
        cls.user = UserFactory()
        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(
            entity=entity_version.entity,
            person__user=cls.user_adri
        )
        cls.user_gf = UserFactory()

        access_perm = Permission.objects.get(name='can_access_partnerships')
        cls.user.user_permissions.add(access_perm)
        cls.user_adri.user_permissions.add(access_perm)
        cls.user_gf.user_permissions.add(access_perm)

        # Years
        cls.start_academic_year = AcademicYearFactory(year=2150)
        cls.from_academic_year = AcademicYearFactory(year=2151)
        cls.end_academic_year = AcademicYearFactory(year=2152)

        # Ucl
        sector = EntityFactory()
        EntityVersionFactory(entity=sector, entity_type=SECTOR)
        cls.ucl_university = EntityFactory()
        EntityVersionFactory(entity=cls.ucl_university, parent=sector, entity_type=FACULTY)
        UCLManagementEntityFactory(entity=cls.ucl_university)
        PartnershipEntityManagerFactory(
            person__user=cls.user_gf,
            entity=cls.ucl_university,
        )

        cls.partnership = PartnershipFactory(
            author=cls.user_gf.person,
            ucl_entity=cls.ucl_university,
        )
        cls.url = resolve_url('partnerships:delete', pk=cls.partnership.pk)

        cls.partnership_with_agreements = PartnershipFactory(
            author=cls.user_gf.person,
            ucl_entity=cls.ucl_university,
        )
        PartnershipAgreementFactory(
            partnership=cls.partnership_with_agreements
        )
        cls.url_with = resolve_url('partnerships:delete',
                                   pk=cls.partnership_with_agreements.pk)

    def test_get_as_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, self.template_name)
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_as_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, self.template_name)
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_as_gf_without_agreements(self):
        self.client.force_login(self.user_gf)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, self.template_name)
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_as_gf_with_agreements(self):
        self.client.force_login(self.user_gf)
        response = self.client.get(self.url_with, follow=True)
        self.assertTemplateNotUsed(response, self.template_name)
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_as_adri_without_agreements(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, self.template_name)

    def test_get_as_adri_with_agreements(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url_with, follow=True)
        self.assertTemplateNotUsed(response, self.template_name)
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_post_as_adri_without_agreements(self):
        self.client.force_login(self.user_adri)
        response = self.client.post(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_list.html')
        self.assertContains(response, _('partnership_success_delete'))
