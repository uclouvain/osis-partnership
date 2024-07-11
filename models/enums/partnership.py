from django.utils.translation import gettext_lazy as _
from base.models.utils.utils import ChoiceEnum


class PartnershipType(ChoiceEnum):
    GENERAL = _('Accord general de collaboration')
    MOBILITY = _('Partenariat de mobilite')
    COURSE = _('Partenariat de co-organisation de formation')
    DOCTORATE = _('Partenariat de co-organisation de doctorat')
    PROJECT = _('Projet finance')

    @classmethod
    def with_synced_dates(cls):
        """ Types for which their start_date and end_date are synchronized
        with the academic_year of their partnership_years """
        return [
            PartnershipType.MOBILITY.name,
            PartnershipType.COURSE.name,
            PartnershipType.DOCTORATE.name,
        ]

class PartnershipDiplomaWithUCL(ChoiceEnum):
    UNIQUE = _('Partenaire unique')
    SEPARED = _('Partenaire séparé')
    NO_CODIPLOMA = _('Non co-diplômant')

    @classmethod
    def get_list_names(cls):
        return [
            PartnershipDiplomaWithUCL.UNIQUE.name,
            PartnershipDiplomaWithUCL.SEPARED.name,
            PartnershipDiplomaWithUCL.NO_CODIPLOMA.name
        ]

class PartnershipProductionSupplement(ChoiceEnum):
    YES = _('Oui')
    NO = _('Non')
    SHARED = _('Partagé')

    @classmethod
    def get_list_names(cls):
        return [
            PartnershipProductionSupplement.YES.name,
            PartnershipProductionSupplement.NO.name,
            PartnershipProductionSupplement.SHARED.name
        ]

