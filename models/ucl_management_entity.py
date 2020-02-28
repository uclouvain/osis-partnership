from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from base.models.entity import Entity

__all__ = ['UCLManagementEntity']


class UCLManagementEntity(models.Model):
    faculty = models.ForeignKey(
        'base.Entity',
        verbose_name=_("faculty"),
        related_name='faculty_managements',
        on_delete=models.CASCADE,
    )
    entity = models.ForeignKey(
        'base.Entity',
        null=True,
        blank=True,
        verbose_name=_("entity"),
        related_name='entity_managements',
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
        verbose_name=_("email"),
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
        verbose_name=_("email"),
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

    class Meta:
        unique_together = ("faculty", "entity")

    def __str__(self):
        if self.entity is None:
            return str(self.faculty)
        return ("{} {}".format(self.faculty, self.entity))

    def is_contact_in_defined(self):
        return (
            self.contact_in_person is not None
            or self.contact_in_email is not None
            or self.contact_in_url is not None
        )

    def is_contact_out_defined(self):
        return (
            self.contact_out_person is not None
            or self.contact_out_email is not None
            or self.contact_out_url is not None
        )

    def are_contacts_defined(self):
        return (
            self.is_contact_in_defined() or self.is_contact_out_defined()
        )

    def has_linked_partnerships(self):
        partnerships = self.faculty.partnerships
        if self.entity is None:
            return partnerships.filter(ucl_university_labo__isnull=True).exists()
        return partnerships.filter(ucl_university_labo=self.entity).exists()

    def validate_unique(self, exclude=None):
        if self.entity is None:  # and hasattr(self, faculty) and self.faculty is not None):
            try:
                if UCLManagementEntity.objects.exclude(id=self.id).filter(
                        faculty=self.faculty,
                        entity__isnull=True,
                ).exists():
                    raise ValidationError(_("duplicate_ucl_management_entity_error_with_faculty"))
            except Entity.DoesNotExist:
                pass
        super().validate_unique(exclude)
