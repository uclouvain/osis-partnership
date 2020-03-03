from django.utils.translation import gettext_lazy as _

from base.models.utils.utils import ChoiceEnum


class PartnershipType(ChoiceEnum):
    INTENTION = _('Déclaration d’intention')
    CADRE = _('Accord-cadre')
    SPECIFIQUE = _('Accord spécifique')
    CODIPLOMATION = _('Accord de co-diplômation')
    COTUTELLE = _('Accord de co-tutelle')
    MOBILITY = ('Partenariat de mobilité')
    FOND_APPUIE = _('Projet Fonds d’appuie à l’internationnalisation')
    AUTRE = _('Autre')
