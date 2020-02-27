from django.db import models
from django.utils.translation import gettext_lazy as _

from partnership.models import AgreementStatus

__all__ = ['PartnershipAgreement']


class PartnershipAgreement(models.Model):
    """
    Accord de partenariat.

    Valable pour un partenariat et une plage d'année académique.
    """
    external_id = models.CharField(
        _('external_id'),
        help_text=_('to_synchronize_with_epc'),
        max_length=255,
        unique=True,
        blank=True,
        null=True,
        editable=False,
    )
    changed = models.DateField(_('changed'), auto_now=True, editable=False)

    partnership = models.ForeignKey(
        'partnership.Partnership',
        verbose_name=_('partnership'),
        on_delete=models.PROTECT,
        related_name='agreements',
    )

    start_academic_year = models.ForeignKey(
        'base.AcademicYear',
        verbose_name=_('start_academic_year'),
        on_delete=models.PROTECT,
        related_name='+',
    )

    end_academic_year = models.ForeignKey(
        'base.AcademicYear',
        verbose_name=_('end_academic_year'),
        on_delete=models.PROTECT,
        related_name='partnership_agreements_end',
    )

    media = models.ForeignKey(
        'partnership.Media',
        verbose_name=_('media'),
        on_delete=models.PROTECT,
        related_name='+',
    )

    status = models.CharField(
        _('status'),
        max_length=10,
        choices=AgreementStatus.choices(),
        default=AgreementStatus.WAITING.name,
    )

    comment = models.TextField(
        _('comment'),
        blank=True,
        default='',
    )

    class Meta:
        verbose_name = _('financing')
        ordering = [
            '-start_academic_year__start_date',
        ]
        permissions = (
            ('can_access_partnerships_agreements', _('can_access_partnerships_agreements')),
        )

    def __str__(self):
        return '{0} > {1}'.format(self.start_academic_year, self.end_academic_year)

    @property
    def is_valid(self):
        return self.status == AgreementStatus.VALIDATED.name
