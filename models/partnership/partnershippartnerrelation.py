from admission import models
from partnership.models import PartnershipDiplomaWithUCL, PartnershipProductionSupplement
from django.utils.translation import gettext_lazy as _


class PartnershipPartnerRelation(models.Model):
    ucl_entity = models.ForeignKey(
        'base.Entity',
        verbose_name=_('ucl_entity'),
        on_delete=models.PROTECT
    )
    partnership = models.ForeignKey(
        'Partnership',
        verbose_name=_('partnership'),
        on_delete=models.PROTECT
    )
    diploma_with_ucl = models.CharField(
        choice = PartnershipDiplomaWithUCL.choices(),
        default = PartnershipDiplomaWithUCL.UNIQUE.name
    )
    diploma_production = models.BooleanField(
        default = False
    )
    supplement_production = models.CharField(
        choice = PartnershipProductionSupplement.choices(),
        default = PartnershipProductionSupplement.NO.name
    )
