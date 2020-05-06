from django.utils.translation import gettext_lazy as _

from base.models.utils.utils import ChoiceEnum


class PartnershipType(ChoiceEnum):
    GENERAL = _('Accord général de collaboration')
    MOBILITY = _('Partenariat de mobilité')
    COURSE = _('Partenariat de co-organisation de formation')
    DOCTORATE = _('Partenariat de co-organisation de doctorat')
    PROJECT = _('Projet financé')
