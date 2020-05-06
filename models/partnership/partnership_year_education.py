from django.db import models
from django.utils.translation import gettext_lazy as _

__all__ = [
    'PartnershipYearEducationLevel',
]


class PartnershipYearEducationLevel(models.Model):
    """
    Niveau d'éducation pour un partenariat et une année académique.

    Administrable dans l'administration Django et possibilité d'en mettre plusieurs.
    """
    code = models.CharField(max_length=30, unique=True)
    label = models.CharField(max_length=255)
    education_group_types = models.ManyToManyField(
        'base.EducationGroupType',
        verbose_name=_('education_group_types'),
        related_name='partnership_education_levels',
    )

    class Meta:
        ordering = ('code',)

    def __str__(self):
        return '{0} - {1}'.format(self.code, self.label)
