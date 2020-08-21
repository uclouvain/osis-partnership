from datetime import date, timedelta

from django.shortcuts import resolve_url
from django.test import TestCase
from django.urls import reverse

from base.models.enums.education_group_types import TrainingType
from base.models.enums.entity_type import FACULTY, SECTOR
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.user import UserFactory
from partnership.models import PartnershipType
from partnership.tests.factories import (
    PartnerEntityFactory,
    PartnerFactory,
    PartnershipEntityManagerFactory,
    PartnershipFactory, PartnershipYearEducationLevelFactory,
    PartnershipYearFactory, UCLManagementEntityFactory,
)
from partnership.tests.factories.partnership_year import (
    PartnershipMissionFactory,
    PartnershipSubtypeFactory,
)
from reference.tests.factories.domain_isced import DomainIscedFactory


class PartnershipCreateDoctorateViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(
            entity=entity_version.entity,
            person__user=cls.user,
            scopes=[PartnershipType.DOCTORATE.name]
        )

        cls.partner = PartnerFactory()
        cls.partner_entity = PartnerEntityFactory(partner=cls.partner)

        AcademicYearFactory.produce_in_future(date.today().year, 3)

        cls.education_field = DomainIscedFactory()
        cls.education_level = PartnershipYearEducationLevelFactory()
        cls.education_level.education_group_types.add(
            EducationGroupTypeFactory(name=TrainingType.PHD.name)
        )

        cls.url = reverse(
            'partnerships:create',
            kwargs={'type': PartnershipType.DOCTORATE},
        )

        # Ucl
        root = EntityVersionFactory(parent=None).entity
        sector = EntityVersionFactory(entity_type=SECTOR, parent=root).entity
        cls.ucl_university = EntityVersionFactory(
            parent=sector,
            entity_type=FACULTY,
        ).entity
        cls.ucl_university_labo = EntityVersionFactory(
            parent=cls.ucl_university,
        ).entity
        UCLManagementEntityFactory(entity=cls.ucl_university)

        cls.university_offer = EducationGroupYearFactory(administration_entity=cls.ucl_university_labo)

        cls.data = {
            'partnership_type': PartnershipType.DOCTORATE.name,
            'comment': '',
            'partner': cls.partner.pk,
            'partner_entity': cls.partner_entity.pk,
            'supervisor': PersonFactory().pk,
            'ucl_entity': cls.ucl_university.pk,
            'university_offers': [cls.university_offer.pk],
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=365),
            'year-education_fields': [cls.education_field.pk],
            'year-entities': [],
            'year-offers': [],
            'year-missions': PartnershipMissionFactory().pk,
            'year-subtype': PartnershipSubtypeFactory().pk,
        }

    def test_get_view_as_adri(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_create.html')

    def test_post(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, data=self.data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_detail.html')


class PartnershipUpdateDoctorateViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(
            entity=entity_version.entity,
            person__user=cls.user,
            scopes=[PartnershipType.DOCTORATE.name]
        )

        # Dates :
        cls.partner = PartnerFactory()
        cls.partner_entity = PartnerEntityFactory(partner=cls.partner)

        # Years
        cls.start_academic_year = AcademicYearFactory(year=2150)
        cls.from_academic_year = AcademicYearFactory(year=2151)
        cls.end_academic_year = AcademicYearFactory(year=2152)

        cls.education_field = DomainIscedFactory()
        cls.education_level = PartnershipYearEducationLevelFactory()
        cls.education_level.education_group_types.add(
            EducationGroupTypeFactory(name=TrainingType.PHD.name)
        )

        # Ucl
        root = EntityVersionFactory(parent=None).entity
        sector = EntityVersionFactory(entity_type=SECTOR, parent=root).entity
        cls.ucl_university = EntityVersionFactory(
            parent=sector,
            entity_type=FACULTY,
        ).entity
        UCLManagementEntityFactory(entity=cls.ucl_university)
        cls.ucl_university_labo = EntityVersionFactory(
            parent=cls.ucl_university,
        ).entity
        UCLManagementEntityFactory(entity=cls.ucl_university_labo)

        cls.partnership = PartnershipFactory(
            partnership_type=PartnershipType.DOCTORATE.name,
            partner=cls.partner,
            partner_entity=cls.partner_entity,
            author=cls.user.person,
            years=[],
            ucl_entity=cls.ucl_university,
        )
        PartnershipYearFactory(
            partnership=cls.partnership,
            academic_year=cls.start_academic_year,
        )
        PartnershipYearFactory(
            partnership=cls.partnership,
            academic_year=cls.from_academic_year,
        )
        PartnershipYearFactory(
            partnership=cls.partnership,
            academic_year=cls.end_academic_year,
        )
        cls.url = resolve_url('partnerships:update', pk=cls.partnership.pk)

        cls.data = {
            'comment': '',
            'partner': cls.partner.pk,
            'partner_entity': cls.partner_entity.pk,
            'supervisor': cls.user.person.pk,
            'ucl_entity': cls.ucl_university_labo.pk,
            'start_date': cls.from_academic_year.start_date,
            'end_date': cls.end_academic_year.end_date,
            'year-education_fields': [cls.education_field.pk],
            'year-entities': [],
            'year-offers': [],
            'year-missions': [
                PartnershipMissionFactory().pk,
                PartnershipMissionFactory().pk,
            ],
            'year-subtype': PartnershipSubtypeFactory().pk,
        }

    def test_get_own_partnership_as_adri(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_update.html')

    def test_post_partnership(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, data=self.data, follow=True)
        self.assertTemplateUsed(response, 'partnerships/partnership/partnership_detail.html')
