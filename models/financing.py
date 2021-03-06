from django.db import models
from django.utils.translation import gettext_lazy as _

__all__ = [
    'Financing',
    'FundingType',
    'FundingProgram',
    'FundingSource',
]


class FinancingManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'type',
            'academic_year',
        )


class Financing(models.Model):
    """
    Un financement pour un/des pays et une année académique.
    """
    countries = models.ManyToManyField(
        'reference.Country',
        verbose_name=_('countries'),
    )
    academic_year = models.ForeignKey(
        'base.AcademicYear',
        verbose_name=_('academic_year'),
        on_delete=models.CASCADE,
    )
    type = models.ForeignKey(
        'partnership.FundingType',
        verbose_name=_('funding_type'),
        on_delete=models.CASCADE,
    )

    objects = FinancingManager()

    class Meta:
        unique_together = (('type', 'academic_year'),)
        ordering = ('academic_year__year',)

    def __str__(self):
        return '{0} - {1}'.format(self.academic_year, self.type)


class FundingTypeManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('program__source')


class FundingType(models.Model):
    name = models.CharField(verbose_name=_('funding_type'), max_length=100)
    url = models.URLField(_('url'), blank=True)
    is_active = models.BooleanField(_('is_active'), default=True)
    program = models.ForeignKey(
        'partnership.FundingProgram',
        verbose_name=_('funding_program'),
        on_delete=models.CASCADE,
    )

    objects = FundingTypeManager()

    class Meta:
        ordering = ('name',)
        verbose_name = _('funding_type')

    def __str__(self):
        return self.name


class FundingProgram(models.Model):
    name = models.CharField(verbose_name=_('funding_program'), max_length=100)
    is_active = models.BooleanField(_('is_active'), default=True)
    source = models.ForeignKey(
        'partnership.FundingSource',
        verbose_name=_('funding_source'),
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _('funding_program')
        ordering = ('name',)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.is_active:
            # Disable all children
            self.fundingtype_set.all().update(is_active=False)


class FundingSource(models.Model):
    name = models.CharField(verbose_name=_('funding_source'), max_length=100)

    class Meta:
        verbose_name = _('funding_source')
        ordering = ('name',)

    def __str__(self):
        return self.name
