from django.utils.translation import gettext_lazy as _
from django.db import models


class PartnershipYearOffers(models.Model):
    """
    Le modèle représentant une relation entre le catalogue de formation et un partenariat
    """
    partnershipyear = models.ForeignKey(
        'partnership.PartnershipYear',
        on_delete=models.CASCADE,
        verbose_name=_('partnership_year'),
        related_name='partnership_year',
    )
    educationgroupyear = models.ForeignKey(
        'base.EducationGroupYear',
        on_delete=models.CASCADE,
        verbose_name=_('education_group_year'),
        related_name='partnership_year_offers',
    )
    educationgroup = models.ForeignKey(
        'base.EducationGroup',
        verbose_name=_('education_group'),
        related_name='partnerships_educationgroup',
        on_delete=models.CASCADE,
        default=None,
        blank=True,
        null=True,
    )

    class Meta:
        db_table = 'partnership_partnershipyear_offers'