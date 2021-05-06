from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import OuterRef, Subquery
from django.utils.translation import gettext_lazy as _

from base.models.entity_version import EntityVersion
from base.models.organization import Organization
from partnership.models import AgreementStatus

__all__ = ['PartnershipAgreement']


class PartnershipAgreementQuerySet(models.QuerySet):
    def annotate_partner_address(self, *fields):
        """
        Add annotations on partner contact address

        :param fields: list of fields relative to EntityVersionAddress
            If a field contains a traversal, e.g. country__name, it will be
            available as country_name
        """
        contact_address_qs = EntityVersion.objects.filter(
            entity__organization=OuterRef('partnership__partner_entities__organization'),
            parent__isnull=True,
        ).order_by('-start_date')
        qs = self
        for field in fields:
            lookup = Subquery(contact_address_qs.values(
                'entityversionaddress__{}'.format(field)
            )[:1])
            qs = qs.annotate(**{field.replace('__', '_'): lookup})
        return qs

    def annotate_partner_name(self):
        """Add annotation on partner name"""
        return self.annotate(
            partner_name=Subquery(Organization.objects.filter(
                pk=OuterRef('partnership__partner_entities__organization'),
            ).values('name')[:1])
        )


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

    start_date = models.DateField(_('start_date'), null=True)
    end_date = models.DateField(_('end_date'), null=True)

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

    objects = PartnershipAgreementQuerySet.as_manager()

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

    def clean(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError(_("End date must be after start date"))
