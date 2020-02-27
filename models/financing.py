from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

__all__ = ['Financing']


class Financing(models.Model):
    """
    Un financement pour un/des pays et une année académique.
    """
    name = models.CharField(_('Name'), max_length=50)
    url = models.URLField(_('url'))
    countries = models.ManyToManyField('reference.Country', verbose_name=_('countries'))
    academic_year = models.ForeignKey(
        'base.AcademicYear',
        verbose_name=_('academic_year'),
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = (('name', 'academic_year'),)
        ordering = ('academic_year__year',)

    def __str__(self):
        return '{0} - {1}'.format(self.academic_year, self.name)

    def get_absolute_url(self):
        return reverse('partnerships:financings:detail', kwargs={'pk': self.pk})
