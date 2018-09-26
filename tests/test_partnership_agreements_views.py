from datetime import date, timedelta

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity_manager import EntityManagerFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.user import UserFactory
from django.test import TestCase
from django.urls import reverse
from partnership.models import Media, PartnershipAgreement
from partnership.tests.factories import (PartnershipAgreementFactory,
                                         PartnershipFactory)


class PartnershipAgreementCreateViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # User creation
        cls.user = UserFactory()
        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PersonEntityFactory(entity=entity_version.entity, person__user=cls.user_adri)
        cls.user_gf = UserFactory()
        entity_manager = EntityManagerFactory(person__user=cls.user_gf)
        cls.user_other_gf = UserFactory()
        EntityManagerFactory(person__user=cls.user_other_gf, entity=entity_manager.entity)
        # Partnership creation
        cls.date_ok = date.today() + timedelta(days=365)
        date_ko = date.today() - timedelta(days=365)
        cls.partnership = PartnershipFactory()
        cls.partnership_gf = PartnershipFactory(author=cls.user_gf)
        cls.partnership_out_of_date = PartnershipFactory(author=cls.user_gf)
        # Misc
        cls.url = reverse('partnerships:agreements:create', kwargs={'partnership_pk': cls.partnership.pk})

    def test_get_view_as_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/agreements/create.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_view_as_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/agreements/create.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_view_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/agreements/create.html')

    def test_get_as_gf(self):
        self.client.force_login(self.user_gf)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/agreements/create.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_own_as_gf(self):
        self.client.force_login(self.user_gf)
        url = reverse('partnerships:agreements:create', kwargs={'partnership_pk': self.partnership_gf.pk})
        response = self.client.get(url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/agreements/create.html')

    def test_get_from_faculty_as_gf(self):
        self.client.force_login(self.user_other_gf)
        url = reverse('partnerships:agreements:create', kwargs={'partnership_pk': self.partnership_gf.pk})
        response = self.client.get(url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/agreements/create.html')

    def test_get_out_of_date_as_adri(self):
        self.client.force_login(self.user_adri)
        url = reverse('partnerships:agreements:create', kwargs={'partnership_pk': self.partnership_out_of_date.pk})
        response = self.client.get(url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/agreements/create.html')

    def test_get_out_of_date_as_gf(self):
        self.client.force_login(self.user_gf)
        url = reverse('partnerships:agreements:create', kwargs={'partnership_pk': self.partnership_out_of_date.pk})
        response = self.client.get(url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/agreements/create.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_post(self):
        self.client.force_login(self.user_adri)
        data = {
            'start_academic_year': AcademicYearFactory(year=self.date_ok.year).pk,
            'end_academic_year': AcademicYearFactory(year=self.date_ok.year + 1).pk,
            'status': PartnershipAgreement.STATUS_WAITING,
            'comment': 'test',
            'media-name': 'test',
            'media-description': 'test',
            'media-url': 'http://example.com',
            'media-visibility': Media.VISIBILITY_PUBLIC,
        }
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership_detail.html')


class PartnershipAgreementsUpdateViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # User creation
        cls.user = UserFactory()
        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PersonEntityFactory(entity=entity_version.entity, person__user=cls.user_adri)
        cls.user_gf = UserFactory()
        entity_manager = EntityManagerFactory(person__user=cls.user_gf)
        cls.user_other_gf = UserFactory()
        EntityManagerFactory(person__user=cls.user_other_gf, entity=entity_manager.entity)
        # Partnership creation
        cls.date_ok = date.today() + timedelta(days=365)
        date_ko = date.today() - timedelta(days=365)
        cls.partnership = PartnershipFactory()
        PartnershipAgreementFactory(partnership=cls.partnership)
        cls.partnership_gf = PartnershipFactory(author=cls.user_gf)
        PartnershipAgreementFactory(partnership=cls.partnership_gf)
        cls.partnership_out_of_date = PartnershipFactory(author=cls.user_gf)
        PartnershipAgreementFactory(partnership=cls.partnership_out_of_date)
        # Misc
        cls.url = reverse('partnerships:agreements:update', kwargs={
            'partnership_pk': cls.partnership.pk, 'pk': cls.partnership.agreements.all()[0].pk
        })

    def test_get_view_as_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/agreements/update.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_view_as_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/agreements/update.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_view_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/agreements/update.html')

    def test_get_as_gf(self):
        self.client.force_login(self.user_gf)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/agreements/update.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_own_as_gf(self):
        self.client.force_login(self.user_gf)
        url = reverse('partnerships:agreements:update', kwargs={
            'partnership_pk': self.partnership_gf.pk, 'pk': self.partnership_gf.agreements.all()[0].pk
        })
        response = self.client.get(url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/agreements/update.html')

    def test_get_from_faculty_as_gf(self):
        self.client.force_login(self.user_other_gf)
        url = reverse('partnerships:agreements:update', kwargs={
            'partnership_pk': self.partnership_gf.pk, 'pk': self.partnership_gf.agreements.all()[0].pk
        })
        response = self.client.get(url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/agreements/update.html')

    def test_get_out_of_date_as_adri(self):
        self.client.force_login(self.user_adri)
        url = reverse('partnerships:agreements:update', kwargs={
            'partnership_pk': self.partnership_out_of_date.pk, 'pk': self.partnership_out_of_date.agreements.all()[0].pk
        })
        response = self.client.get(url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/agreements/update.html')

    def test_get_out_of_date_as_gf(self):
        self.client.force_login(self.user_gf)
        url = reverse('partnerships:agreements:update', kwargs={
            'partnership_pk': self.partnership_out_of_date.pk, 'pk': self.partnership_out_of_date.agreements.all()[0].pk
        })
        response = self.client.get(url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/agreements/update.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_post(self):
        self.client.force_login(self.user_adri)
        data = {
            'start_academic_year': AcademicYearFactory(year=self.date_ok.year).pk,
            'end_academic_year': AcademicYearFactory(year=self.date_ok.year + 1).pk,
            'status': PartnershipAgreement.STATUS_WAITING,
            'comment': 'test',
            'media-name': 'test',
            'media-description': 'test',
            'media-url': 'http://example.com',
            'media-visibility': Media.VISIBILITY_PUBLIC,
        }
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership_detail.html')


class PartnershipAgreementsDeleteViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # User creation
        cls.user = UserFactory()
        cls.user_adri = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PersonEntityFactory(entity=entity_version.entity, person__user=cls.user_adri)
        cls.user_gf = UserFactory()
        entity_manager = EntityManagerFactory(person__user=cls.user_gf)
        cls.user_other_gf = UserFactory()
        EntityManagerFactory(person__user=cls.user_other_gf, entity=entity_manager.entity)
        # Partnership creation
        cls.date_ok = date.today() + timedelta(days=365)
        date_ko = date.today() - timedelta(days=365)
        cls.partnership = PartnershipFactory()
        PartnershipAgreementFactory(partnership=cls.partnership)
        cls.partnership_gf = PartnershipFactory(author=cls.user_gf)
        PartnershipAgreementFactory(partnership=cls.partnership_gf)
        cls.partnership_out_of_date = PartnershipFactory(author=cls.user_gf)
        PartnershipAgreementFactory(partnership=cls.partnership_out_of_date)
        # Misc
        cls.url = reverse('partnerships:agreements:delete', kwargs={
            'partnership_pk': cls.partnership.pk, 'pk': cls.partnership.agreements.all()[0].pk
        })

    def test_get_view_as_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/agreements/delete.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_view_as_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/agreements/delete.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_view_as_adri(self):
        self.client.force_login(self.user_adri)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/agreements/delete.html')

    def test_get_as_gf(self):
        self.client.force_login(self.user_gf)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/agreements/delete.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_get_own_as_gf(self):
        self.client.force_login(self.user_gf)
        url = reverse('partnerships:agreements:delete', kwargs={
            'partnership_pk': self.partnership_gf.pk, 'pk': self.partnership_gf.agreements.all()[0].pk
        })
        response = self.client.get(url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/agreements/delete.html')

    def test_get_from_faculty_as_gf(self):
        self.client.force_login(self.user_other_gf)
        url = reverse('partnerships:agreements:delete', kwargs={
            'partnership_pk': self.partnership_gf.pk, 'pk': self.partnership_gf.agreements.all()[0].pk
        })
        response = self.client.get(url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/agreements/delete.html')

    def test_get_out_of_date_as_adri(self):
        self.client.force_login(self.user_adri)
        url = reverse('partnerships:agreements:delete', kwargs={
            'partnership_pk': self.partnership_out_of_date.pk, 'pk': self.partnership_out_of_date.agreements.all()[0].pk
        })
        response = self.client.get(url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/agreements/delete.html')

    def test_get_out_of_date_as_gf(self):
        self.client.force_login(self.user_gf)
        url = reverse('partnerships:agreements:delete', kwargs={
            'partnership_pk': self.partnership_out_of_date.pk, 'pk': self.partnership_out_of_date.agreements.all()[0].pk
        })
        response = self.client.get(url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/agreements/delete.html')
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_post(self):
        self.client.force_login(self.user_adri)
        data = {}
        response = self.client.post(self.url, data=data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership_detail.html')
