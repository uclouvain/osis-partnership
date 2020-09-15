from django.utils.translation import gettext_lazy as _

from base.models.utils.utils import ChoiceEnum


class PartnershipType(ChoiceEnum):
    GENERAL = _('Accord général de collaboration')
    MOBILITY = _('Partenariat de mobilité')
    COURSE = _('Partenariat de co-organisation de formation')
    DOCTORATE = _('Partenariat de co-organisation de doctorat')
    PROJECT = _('Projet financé')

    @classmethod
    def with_synced_dates(cls):
        """ Types for which their start_date and end_date are synchronized
        with the academic_year of their partnership_years """
        return [
            PartnershipType.MOBILITY.name,
            PartnershipType.COURSE.name,
            PartnershipType.DOCTORATE.name,
        ]
