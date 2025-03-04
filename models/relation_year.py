from django.db import models
from partnership.models import  PartnershipDiplomaWithUCL, PartnershipProductionSupplement
from django.utils.translation import gettext_lazy as _

__all__ = ['PartnershipPartnerRelationYear']


class PartnershipPartnerRelationYear(models.Model):
    """
    Le modèle représentant une relation annuelle entre une entité et un partenariat
    """
    partnership_relation = models.ForeignKey(
        'partnership.PartnershipPartnerRelation',
        related_name='partnershiprelation',
        on_delete=models.CASCADE,
    )
    academic_year = models.ForeignKey(
        'base.AcademicYear',
        verbose_name=_('academic_year'),
        on_delete=models.PROTECT,
        related_name='+',
    )
    type_diploma_by_partner = models.CharField(
        max_length=64,
        verbose_name=_('type_diploma_by_partner'),
        choices=PartnershipDiplomaWithUCL.choices(),
        null=False,
        blank=True,
        default=''
    )
    diploma_prod_by_partner = models.BooleanField(
        verbose_name=_('diploma_prod_by_partner'),
        default=False
    )
    supplement_prod_by_partner = models.CharField(
        max_length=64,
        verbose_name=_('supplement_prod_by_partner'),
        choices=PartnershipProductionSupplement.choices(),
        null=False,
        blank=True,
        default=''
    )
    partner_referent = models.BooleanField(
        verbose_name=_('partner_referent'),
        default=False
    )

    class Meta:
        unique_together = ['partnership_relation', 'academic_year']
