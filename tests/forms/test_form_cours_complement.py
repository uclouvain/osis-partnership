from django.test import TestCase
from base.models.enums.entity_type import SECTOR, FACULTY
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from partnership.forms import PartnershipCourseForm
from partnership.forms.partnership.partnership import PartnershipPartnerRelationForm, PartnershipPartnerRelationFormSet
from partnership.models import  PartnershipDiplomaWithUCL, PartnershipProductionSupplement
from partnership.tests.factories import PartnershipYearEducationLevelFactory, PartnerEntityFactory, PartnerFactory, \
    PartnershipFactory
from partnership.tests.factories.parternship_partner_relation import PartnerEntityRelationFactory
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
        # Specific PartnershipCourseForm
        self.assertIn("ucl_reference", form.fields)
        self.assertIn("partner_referent", form.fields)
        self.assertIn("all_student", form.fields)
        self.assertIn("diploma_prod_by_ucl", form.fields)
        self.assertIn("diploma_by_ucl", form.fields)
        self.assertIn("supplement_prod_by_ucl", form.fields)

        self.assertIn("subtype", form.fields)
        self.assertIn("description", form.fields)
        self.assertIn("project_acronym", form.fields)
        self.assertIn("supplement_prod_by_ucl", form.fields)

        # Not In
        self.assertNotIn("supplement_prod", form.fields)

    # def test_partnership_course_form_post(self):
    #     """Test que le formulaire valide correctement les données valides"""
    #     data = {
    #             'partnership_type': PartnershipType.COURSE.name,
    #             'comment': '',
    #             'partner': self.partner.pk,
    #             'partner_entities': [self.partner_entity.entity_id],
    #             'supervisor': PersonFactory().pk,
    #             'ucl_entity': self.ucl_university.pk,
    #             'university_offers': [self.university_offer.pk],
    #             'year-education_fields': [self.education_field.pk],
    #             'year-education_levels': [self.education_level.pk],
    #             'year-entities': [],
    #             'year-offers': [],
    #             'year-start_academic_year': self.start_academic_year.pk,
    #             'year-end_academic_year': self.end_academic_year.pk,
    #             'year-funding_type': FundingTypeFactory().pk,
    #             'missions_id': PartnershipMissionFactory().pk,
    #             'subtype_id': PartnershipSubtypeFactory().pk,
    #             'all_student': True,
    #             'ucl_reference': True,
    #             'diploma_prod_by_ucl': True,
    #             'diploma_by_ucl': PartnershipDiplomaWithUCL.SEPARED.name,
    #             'supplement_prod_by_ucl': PartnershipProductionSupplement.SHARED.name,
    #             }
    #
    #     form = PartnershipCourseForm(data=data, initial={"partnership_type":PartnershipType.COURSE.name})
    #     print(form.errors)
    #     self.assertTrue(form.is_valid())


# Factory pour Partnership
class PartnershipPartnerRelationFormTests(TestCase):

    def setUp(self):
        # Utilisation des factories pour créer les instances nécessaires
        self.partnership = PartnershipFactory()
        self.entity = PartnerEntityFactory(partner=PartnerFactory())

    def test_form_initialization(self):
        """Test que le formulaire s'initialise correctement avec les champs spécifiés"""
        form = PartnershipPartnerRelationForm()
        self.assertIn('diploma_with_ucl_by_partner', form.fields)
        self.assertIn('diploma_prod_by_partner', form.fields)
        self.assertIn('supplement_prod_by_partner', form.fields)
        self.assertIn('partnership', form.fields)
        # Not In
        self.assertNotIn("partnerships", form.fields)

    def test_form_validation_success(self):
        """Test que le formulaire valide correctement les données valides"""
        form_data = {
            'diploma_with_ucl_by_partner': PartnershipDiplomaWithUCL.NO_CODIPLOMA.name,
            'diploma_prod_by_partner': True,
            'supplement_prod_by_partner': PartnershipProductionSupplement.SHARED.name,
            'partnership': self.partnership,
            'entity': self.entity
        }
        form = PartnershipPartnerRelationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_validation_failure(self):
        """Test que le formulaire ne valide pas des données invalides"""
        form_data = {
            'diploma_with_ucl_by_partner': 'test',
            'diploma_prod_by_partner': False,
            'supplement_prod_by_partner': 'test',
            'partnership': self.partnership,
            'entity': self.entity
        }
        form = PartnershipPartnerRelationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('diploma_with_ucl_by_partner', form.errors)
        self.assertIn('supplement_prod_by_partner', form.errors)


class PartnershipPartnerRelationFormSetTests(TestCase):

    def setUp(self):
        self.partnership = PartnershipFactory()
        self.entity = EntityFactory()
        self.relation = PartnerEntityRelationFactory(partnership=self.partnership, entity=self.entity)

    def test_formset_initialization(self):
        """Test que le formset s'initialise correctement"""
        formset = PartnershipPartnerRelationFormSet()
        self.assertEqual(len(formset.forms), 2)
        self.assertIn('diploma_with_ucl_by_partner', formset.forms[0].fields)

    # def test_formset_validation_success(self):
    #     """Test que le formset valide correctement les données valides"""
    #     formset_data = {
    #         'form-TOTAL_FORMS': 1,
    #         'form-INITIAL_FORMS': 0,
    #         'form-0-id': self.relation.id,
    #         'form-0-diploma_with_ucl_by_partner': 'UNIQUE',
    #         'form-0-diploma_prod_by_partner': True,
    #         'form-0-supplement_prod_by_partner': 'Yes',
    #         'form-0-partnership': self.partnership,
    #         'form-0-partnership': self.entity
    #     }
    #     formset = PartnershipPartnerRelationFormSet(data=formset_data)
    #     self.assertTrue(formset.is_valid())

    # def test_formset_validation_failure(self):
    #     """Test que le formset ne valide pas des données invalides"""
    #     formset_data = {
    #         'form-0-id': self.relation.id,
    #         'form-0-diploma_with_ucl_by_partner': 'invalid_choice',
    #         'form-0-diploma_prod_by_partner': 'not_boolean',
    #         'form-0-supplement_prod_by_partner': 'invalid_choice',
    #         'form-0-partnership': self.partnership.id
    #     }
    #     formset = PartnershipPartnerRelationFormSet(data=formset_data, queryset=PartnershipPartnerRelation.objects.all())
    #     self.assertFalse(formset.is_valid())
    #     self.assertIn('diploma_with_ucl_by_partner', formset.forms[0].errors)
    #     self.assertIn('diploma_prod_by_partner', formset.forms[0].errors)
    #     self.assertIn('supplement_prod_by_partner', formset.forms[0].errors)
