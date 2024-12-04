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
    UNIQUE = _('Unique conjoint')
    SEPARED = _('Séparé')
    NO_CODIPLOMA = _('Non co-diplômant')
    SHARED = _('Partagé')


class PartnershipProductionSupplement(ChoiceEnum):
    YES = _('Oui')
    NO = _('Non')
    SHARED = _('Partagé')
