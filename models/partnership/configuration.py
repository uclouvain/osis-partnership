from django.db import models
from django.db.models import Subquery, F
from django.utils.translation import gettext_lazy as _

from base.models.academic_year import AcademicYear

__all__ = ['PartnershipConfiguration']


class PartnershipConfiguration(models.Model):
    """
    Configurations diverses concernant les partenariats et modifiable depuis l'interface d'OSIS.
    """
    DAYS_CHOICES = [(day, day) for day in range(1, 32)]
    MONTHS_CHOICES = (
        (1, _('january')),
        (2, _('february')),
        (3, _('march')),
        (4, _('april')),
        (5, _('may')),
        (6, _('june')),
        (7, _('july')),
        (8, _('august')),
        (9, _('september')),
        (10, _('october')),
        (11, _('november')),
        (12, _('december')),
    )

    partnership_creation_update_min_year = models.ForeignKey(
        'base.AcademicYear',
        verbose_name=_('partnership_creation_update_min_year'),
        on_delete=models.PROTECT,
        null=True,
        related_name='+',
    )

    partnership_api_year = models.ForeignKey(
        'base.AcademicYear',
        verbose_name=_('partnership_api_year'),
        on_delete=models.PROTECT,
        null=True,
        related_name='+',
    )

    email_notification_to = models.EmailField(
        _('partnership_email_notification_to'),
        default='programmes.mobilite@uclouvain.be',
    )

    @staticmethod
    def get_configuration():
        try:
            return PartnershipConfiguration.objects.select_related(
                'partnership_api_year',
                'partnership_creation_update_min_year',
            ).get()
        except PartnershipConfiguration.DoesNotExist:
            # By default, mostly for tests, select the logical academic years
            qs = AcademicYear.objects.annotate(
                current_year=Subquery(AcademicYear.objects.currents().values('year')[:1]),
            )
            year = qs.filter(year=F('current_year')).first()
            next_year = qs.filter(year=F('current_year') + 1).first()
            return PartnershipConfiguration.objects.create(
                partnership_creation_update_min_year=next_year,
                partnership_api_year=year,
            )

    def get_current_academic_year_for_creation_modification(self):
        return self.partnership_creation_update_min_year

    def get_current_academic_year_for_api(self):
        return self.partnership_api_year
