from datetime import date

from django.db import models
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

    partnership_creation_update_max_date_day = models.IntegerField(
        _('partnership_creation_update_max_date_day'),
        choices=DAYS_CHOICES,
        default=31,
    )

    partnership_creation_update_max_date_month = models.IntegerField(
        _('partnership_creation_update_max_date_month'),
        choices=MONTHS_CHOICES,
        default=12,
    )

    partnership_api_max_date_day = models.IntegerField(
        _('partnership_api_max_date_day'),
        choices=DAYS_CHOICES,
        default=31,
    )

    partnership_api_max_date_month = models.IntegerField(
        _('partnership_api_max_date_month'),
        choices=MONTHS_CHOICES,
        default=12,
    )

    email_notification_to = models.EmailField(
        _('partnership_email_notification_to'),
        default='programmes.mobilite@uclouvain.be',
    )

    @staticmethod
    def get_configuration():
        try:
            return PartnershipConfiguration.objects.get()
        except PartnershipConfiguration.DoesNotExist:
            return PartnershipConfiguration.objects.create()

    def get_current_academic_year_for_creation_modification(self):
        limit_date = date(
            date.today().year,
            self.partnership_creation_update_max_date_month,
            self.partnership_creation_update_max_date_day,
        )
        if date.today() <= limit_date:
            return AcademicYear.objects.filter(year=date.today().year + 1).first()
        else:
            return AcademicYear.objects.filter(year=date.today().year + 2).first()

    def get_current_academic_year_for_api(self):
        # TODO: Use event calendar instead of current_academic_year/starting_academic_year
        return AcademicYear.objects.get(year=2020)  # BUG: OP-348 - dirty fix
        # limit_date = date(
        #     date.today().year,
        #     self.partnership_api_max_date_month,
        #     self.partnership_api_max_date_day,
        # )
        # if date.today() <= limit_date:
        #     return academic_year.current_academic_year()
        # else:
        #     return academic_year.starting_academic_year()
