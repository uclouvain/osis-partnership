from datetime import timedelta

from django.test import tag
from django.urls import reverse
from django.utils import timezone

from base.models.enums.organization_type import RESEARCH_CENTER
from partnership.tests import TestCase
from partnership.tests.factories import (
    PartnerFactory,
    PartnerTagFactory, PartnershipEntityManagerFactory,
)


class PartnersListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.partner_erasmus_last = PartnerFactory(
            erasmus_code='ZZZ',
        )
        cls.partner_name = PartnerFactory(
            organization__name='foobar',
        )
        cls.partner_partner_type = PartnerFactory(
            organization__type=RESEARCH_CENTER,
        )
        cls.partner_pic_code = PartnerFactory(
            pic_code='foobar',
        )
        cls.partner_erasmus_code = PartnerFactory(
            erasmus_code='foobar',
        )
        cls.partner_is_valid = PartnerFactory(
            is_valid=False,
        )
        cls.partner_not_active = PartnerFactory(
            dates__end=timezone.now() - timedelta(days=1),
        )
        cls.partner_not_active2 = PartnerFactory(
            dates__start=timezone.now() + timedelta(days=1),
        )
        cls.partner_tag = PartnerTagFactory()
        cls.partner_tags = PartnerFactory(
            tags=[cls.partner_tag],
        )
        cls.user = PartnershipEntityManagerFactory().person.user
        cls.url = reverse('partnerships:partners:list')

    def test_get_list_anonymous(self):
        response = self.client.get(self.url, follow=True)
        self.assertTemplateNotUsed(response, 'partnerships/partners/partners_list.html')
        self.assertTemplateUsed(response, 'access_denied.html')

    @tag('perf')
    def test_get_list_authenticated(self):
        self.client.force_login(self.user)
        with self.assertNumQueriesLessThan(24):
            response = self.client.get(self.url)
            self.assertTemplateUsed(response, 'partnerships/partners/partners_list.html')

    @tag('perf')
    def test_num_queries_serializer(self):
        self.client.force_login(self.user)
        with self.assertNumQueriesLessThan(10):
            self.client.get(self.url, headers={"accept": 'application/json'})

    def test_get_list_ordering(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?ordering=-erasmus_code')
        self.assertTemplateUsed(response, 'partnerships/partners/partners_list.html')
        context = response.context_data
        self.assertEqual(context['partners'][0], self.partner_erasmus_last)

    def test_filter_name(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?name=foo')
        self.assertTemplateUsed(response, 'partnerships/partners/partners_list.html')
        context = response.context_data
        self.assertEqual(len(context['partners']), 1)
        self.assertEqual(context['partners'][0], self.partner_name)

    def test_filter_partner_type(self):
        self.client.force_login(self.user)
        url = self.url + '?partner_type={0}'.format(RESEARCH_CENTER)
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'partnerships/partners/partners_list.html')
        context = response.context_data
        self.assertEqual(len(context['partners']), 1)
        self.assertEqual(context['partners'][0], self.partner_partner_type)

    def test_filter_pic_code(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?pic_code=foo')
        self.assertTemplateUsed(response, 'partnerships/partners/partners_list.html')
        context = response.context_data
        self.assertEqual(len(context['partners']), 1)
        self.assertEqual(context['partners'][0], self.partner_pic_code)

    def test_filter_erasmus_code(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?erasmus_code=foo')
        self.assertTemplateUsed(response, 'partnerships/partners/partners_list.html')
        context = response.context_data
        self.assertEqual(len(context['partners']), 1)
        self.assertEqual(context['partners'][0], self.partner_erasmus_code)

    def test_filter_is_valid(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?is_valid=False')
        self.assertTemplateUsed(response, 'partnerships/partners/partners_list.html')
        context = response.context_data
        self.assertEqual(len(context['partners']), 1)
        self.assertEqual(context['partners'][0], self.partner_is_valid)

    def test_filter_is_actif(self):
        self.assertFalse(self.partner_not_active.is_actif)
        self.assertFalse(self.partner_not_active2.is_actif)
        self.client.force_login(self.user)
        response = self.client.get(self.url + '?is_actif=3')
        self.assertTemplateUsed(response, 'partnerships/partners/partners_list.html')
        context = response.context_data
        self.assertEqual(len(context['partners']), 2)
        self.assertEqual(context['partners'][0], self.partner_not_active)
        self.assertEqual(context['partners'][1], self.partner_not_active2)

        response = self.client.get(self.url + '?is_actif=2')
        self.assertTemplateUsed(response, 'partnerships/partners/partners_list.html')
        context = response.context_data
        self.assertEqual(len(context['partners']), 7)

    def test_filter_tags(self):
        self.client.force_login(self.user)
        url = self.url + '?tags={0}'.format(self.partner_tag.pk)
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'partnerships/partners/partners_list.html')
        context = response.context_data
        self.assertEqual(len(context['partners']), 1)
        self.assertEqual(context['partners'][0], self.partner_tags)


class PartnersExportViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.partner_erasmus_last = PartnerFactory(erasmus_code='ZZZ')
        cls.partner_name = PartnerFactory(organization__name='foobar')
        cls.partner_partner_type = PartnerFactory()
        cls.partner_pic_code = PartnerFactory(pic_code='foobar')
        cls.partner_erasmus_code = PartnerFactory(erasmus_code='foobar')
        cls.partner_is_valid = PartnerFactory(is_valid=False)
        cls.partner_is_actif = PartnerFactory(
            dates__end=timezone.now() - timedelta(days=1),
        )
        cls.partner_tags = PartnerFactory()
        cls.user = PartnershipEntityManagerFactory().person.user
        cls.url = reverse('partnerships:partners:export')

    def test_get_list_anonymous(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_get_list_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
