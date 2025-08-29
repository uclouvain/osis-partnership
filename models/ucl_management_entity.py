from django.db import models
from django.utils.translation import gettext_lazy as _, pgettext_lazy

__all__ = ['UCLManagementEntity']


class UCLManagementEntity(models.Model):
    entity = models.OneToOneField(
        'base.Entity',
        verbose_name=_("entity"),
        related_name='uclmanagement_entity',
        on_delete=models.CASCADE
    )
    academic_responsible = models.ForeignKey(
        'base.Person',
        related_name='management_entities',
        verbose_name=_("academic_responsible"),
        on_delete=models.CASCADE
    )
    administrative_responsible = models.ForeignKey(
        'base.Person',
        related_name='+',
        verbose_name=_("administrative_responsible"),
        on_delete=models.CASCADE
    )
    contact_in_person = models.ForeignKey(
        'base.Person',
        related_name='+',
        null=True,
        blank=True,
        verbose_name=_("contact_in_name"),
        on_delete=models.CASCADE
    )
    contact_in_email = models.EmailField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("partnership", "email"),
    )
    contact_in_url = models.URLField(
        null=True,
        blank=True,
        verbose_name=_("portal"),
    )
    contact_out_person = models.ForeignKey(
        'base.Person',
        related_name='+',
        null=True,
        blank=True,
        verbose_name=_("contact_out_name"),
        on_delete=models.CASCADE
    )
    contact_out_email = models.EmailField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("partnership", "email"),
    )
    contact_out_url = models.URLField(
        null=True,
        blank=True,
        verbose_name=_("portal")
    )

    course_catalogue_text_fr = models.TextField(
        _('course_catalogue_text_fr'),
        blank=True,
        default='',
    )
    course_catalogue_text_en = models.TextField(
        _('course_catalogue_text_en'),
        blank=True,
        default='',
    )
    course_catalogue_url_fr = models.URLField(
        _('course_catalogue_url_fr'),
        blank=True,
        default='',
    )
    course_catalogue_url_en = models.URLField(
        _('course_catalogue_url_en'),
        blank=True,
        default='',
    )

    def __str__(self):
        return str(self.entity)

    def is_contact_in_defined(self):
        return (
            self.contact_in_person_id is not None
            or self.contact_in_email is not None
            or self.contact_in_url is not None
        )

    def is_contact_out_defined(self):
        return (
            self.contact_out_person_id is not None
            or self.contact_out_email is not None
            or self.contact_out_url is not None
        )

    def are_contacts_defined(self):
        return (
            self.is_contact_in_defined() or self.is_contact_out_defined()
        )
