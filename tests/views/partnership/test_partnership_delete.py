from django.shortcuts import resolve_url
from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from base.models.enums.entity_type import FACULTY, SECTOR
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from partnership.tests.factories import (
    PartnershipAgreementFactory, PartnershipEntityManagerFactory,
    PartnershipFactory,
    UCLManagementEntityFactory,
)
from partnership.tests.factories.viewer import PartnershipViewerFactory


class PartnershipDeleteViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.template_name = 'partnerships/partnership/partnership_confirm_delete.html'

        # Ucl
        sector = EntityFactory()
        EntityVersionFactory(entity=sector, entity_type=SECTOR)
        cls.ucl_university = EntityFactory()
        EntityVersionFactory(entity=cls.ucl_university, parent=sector, entity_type=FACULTY)
        UCLManagementEntityFactory(entity=cls.ucl_university)

        # Users
        cls.user = PartnershipViewerFactory().person.user
        cls.user_gf = PartnershipEntityManagerFactory(
            entity=cls.ucl_university,
        ).person.user
        cls.user_adri = PartnershipEntityManagerFactory(
            entity=EntityVersionFactory(acronym='ADRI').entity,
        ).person.user

        # Years
        cls.start_academic_year = AcademicYearFactory(year=2150)
        cls.from_academic_year = AcademicYearFactory(year=2151)
        cls.end_academic_year = AcademicYearFactory(year=2152)

        # Partnerships
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
