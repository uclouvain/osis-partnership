from django.contrib.auth.models import Permission
from django.test import TestCase
from base.models.enums.entity_type import SECTOR, FACULTY
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.user import UserFactory
from partnership.forms import PartnershipCourseForm, PartnershipYearCourseForm
from partnership.forms.partnership.year import PartnerRelationYearFormSet

from partnership.models import PartnershipDiplomaWithUCL, PartnershipProductionSupplement, PartnershipType
from partnership.models.relation_year import PartnershipPartnerRelationYear
from partnership.tests.factories import (PartnershipYearEducationLevelFactory, PartnerEntityFactory, PartnerFactory,
                                         FundingTypeFactory, PartnershipSubtypeFactory,PartnershipEntityManagerFactory)
from partnership.tests.factories.parternship_partner_relation import PartnershipPartnerRelationYearFactory

from reference.tests.factories.domain_isced import DomainIscedFactory


class TestPartnershipCourseForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Ucl
        root = EntityVersionFactory(parent=None, entity_type='').entity
        sector = EntityVersionFactory(entity_type=SECTOR, parent=root).entity
        cls.ucl_university = EntityVersionFactory(
            parent=sector,
            entity_type=FACULTY,
        ).entity

        cls.ucl_university_labo = EntityVersionFactory(
            parent=cls.ucl_university,
        ).entity
        cls.university_offer = EducationGroupYearFactory(administration_entity=cls.ucl_university_labo)

        cls.education_field = DomainIscedFactory()
        cls.education_level = PartnershipYearEducationLevelFactory()

        # Patner
        cls.partner = PartnerFactory()
        cls.partner_entity = PartnerEntityFactory(partner=cls.partner)

        # AcademicYear
        cls.start_academic_year = AcademicYearFactory(year=2150)
        cls.end_academic_year = AcademicYearFactory(year=2151)

        #
        cls.subtype = PartnershipSubtypeFactory(types=[
            PartnershipType.COURSE.name,
        ])

        cls.entity = EntityFactory()

    def test_partnership_course_form(self):
        """Test que le formulaire COURSE s'initialise correctement avec les champs spécifiés"""
        form = PartnershipCourseForm(initial={'subtype': "COURSE"})
        # Heritage PartnershipBaseForm
        self.assertIn("partnership_type", form.fields)
        self.assertIn("partner_entities", form.fields)
        self.assertIn("ucl_entity", form.fields)
        self.assertIn("supervisor", form.fields)
        self.assertIn("comment", form.fields)
        self.assertIn("tags", form.fields)
        self.assertIn("is_public", form.fields)
        self.assertIn("missions", form.fields)
        self.assertIn("subtype", form.fields)
        self.assertIn("description", form.fields)
        self.assertIn("project_acronym", form.fields)

        # Not In
        self.assertNotIn("supplement_prod_by_ucl", form.fields)


class TestPartnershipYearCourseForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        entity_version = EntityVersionFactory(acronym='ADRI')
        PartnershipEntityManagerFactory(
            entity=entity_version.entity,
            person__user=cls.user,
            scopes=[PartnershipType.COURSE.name, PartnershipType.GENERAL.name]
        )

        # Création des entités UCL
        root = EntityVersionFactory(parent=None, entity_type='').entity
        sector = EntityVersionFactory(entity_type='SECTOR', parent=root).entity
        cls.ucl_university = EntityVersionFactory(parent=sector, entity_type='FACULTY').entity
        cls.ucl_university_labo = EntityVersionFactory(parent=cls.ucl_university).entity
        cls.university_offer = EducationGroupYearFactory(administration_entity=cls.ucl_university_labo)

        cls.education_field = DomainIscedFactory()
        cls.education_level = PartnershipYearEducationLevelFactory()

        # Création des entités partenaires
        cls.partner = PartnerFactory()
        cls.partner_entity = PartnerEntityFactory(partner=cls.partner)

        # Création des années académiques
        cls.start_academic_year = AcademicYearFactory(year=2150)
        cls.end_academic_year = AcademicYearFactory(year=2151)

        # Création d'un sous-type de partenariat
        cls.subtype = PartnershipSubtypeFactory(types=[PartnershipType.COURSE.name])

        # Données du formulaire
        cls.data = {
            'partnership_type': PartnershipType.COURSE.name,
            'comment': '',
            'partner': cls.partner.pk,
            'partner_entities': [cls.partner_entity.entity_id],
            'supervisor': PersonFactory().pk,
            'ucl_entity': cls.ucl_university.pk,
            'university_offers': [cls.university_offer.pk],
            'education_fields': [cls.education_field.pk],
            'education_levels': [cls.education_level.pk],
            'entities': [],
            'offers': [],
            'start_academic_year': cls.start_academic_year.pk,
            'end_academic_year': cls.end_academic_year.pk,
            'funding_type': FundingTypeFactory().pk,
            'missions': [3, 2],
            'subtype': '',
            'all_student': True,
            'ucl_reference': True,
            'diploma_prod_by_ucl': True,
            'type_diploma_by_ucl': PartnershipDiplomaWithUCL.SEPARED.name,
            'supplement_prod_by_ucl': PartnershipProductionSupplement.SHARED.name,
        }

    def test_partnership_year_course_form_valid(self):
        form = PartnershipYearCourseForm(data=self.data, user = self.user)
        self.assertTrue(form.is_valid(), form.errors)  # Vérifie que le formulaire est valide

    def test_partnership_year_course_form_missing_required_fields(self):
        invalid_data = self.data.copy()
        del invalid_data['type_diploma_by_ucl']  # Suppression d'un champ obligatoire

        form = PartnershipYearCourseForm(data=invalid_data, user = self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("type_diploma_by_ucl", form.errors)  # Vérifie que l'erreur est bien remontée

    def test_partnership_year_course_form_fields(self):
        form = PartnershipYearCourseForm(user = self.user)
        expected_fields = {
            "education_fields","education_levels", "entities", "offers",
            "start_academic_year", "end_academic_year",
            "all_student", "ucl_reference",
            "diploma_prod_by_ucl", "type_diploma_by_ucl",
            "supplement_prod_by_ucl" , 'entity'
        }
        self.assertTrue(expected_fields.issubset(set(form.fields.keys()))) # Vérifie que les champs sont attendus


class TestPartnershipRelationFormSet(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Créer des objets de test pour le formset
        cls.relation_year1 = PartnershipPartnerRelationYearFactory()
        cls.relation_year2 = PartnershipPartnerRelationYearFactory()

        # Structure des données pour le formset
        cls.formset_data = {
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-0-partnership_relation': cls.relation_year1.partnership_relation.pk,
            'form-0-academic_year': cls.relation_year1.academic_year.pk,
            'form-0-type_diploma_by_partner': cls.relation_year1.type_diploma_by_partner,
            'form-0-diploma_prod_by_partner': cls.relation_year1.diploma_prod_by_partner,
            'form-0-supplement_prod_by_partner': cls.relation_year1.supplement_prod_by_partner,
            'form-0-partner_referent': cls.relation_year1.partner_referent,
            'form-1-partnership_relation': cls.relation_year2.partnership_relation.pk,
            'form-1-academic_year': cls.relation_year2.academic_year.pk,
            'form-1-type_diploma_by_partner': cls.relation_year2.type_diploma_by_partner,
            'form-1-diploma_prod_by_partner': cls.relation_year2.diploma_prod_by_partner,
            'form-1-supplement_prod_by_partner': cls.relation_year2.supplement_prod_by_partner,
            'form-1-partner_referent': cls.relation_year2.partner_referent,
        }

    def test_partnership_relation_formset_valid(self):
        formset = PartnerRelationYearFormSet(data=self.formset_data)
        self.assertTrue(formset.is_valid())

    def test_partnership_relation_formset_additional_forms(self):
        formset_data_additional = self.formset_data.copy()
        formset_data_additional['form-2-partnership_relation'] = self.relation_year1.partnership_relation.pk
        formset_data_additional['form-2-academic_year'] = self.relation_year1.academic_year.pk
        formset_data_additional['form-2-type_diploma_by_partner'] = self.relation_year1.type_diploma_by_partner
        formset_data_additional['form-2-diploma_prod_by_partner'] = self.relation_year1.diploma_prod_by_partner
        formset_data_additional['form-2-supplement_prod_by_partner'] = self.relation_year1.supplement_prod_by_partner
        formset_data_additional['form-2-partner_referent'] = self.relation_year1.partner_referent
        formset_data_additional['form-TOTAL_FORMS'] = '3'

        formset = PartnerRelationYearFormSet(data=formset_data_additional)
        self.assertTrue(formset.is_valid())
        self.assertEqual(formset.total_form_count(), 3)  # Vérifier que trois formulaires sont présents