from django.db import models
from django.db.models import Func
from django.utils.translation import gettext_lazy as _

from django_cte import CTEManager

from base.models.entity_version import EntityVersion

__all__ = ['UCLManagementEntity', 'children_of_managed_entities']


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

    objects = CTEManager()

    def __str__(self):
        return str(self.entity)

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
        if hasattr(self.entity, 'partnerships'):
            # That's a faculty
            return self.entity.partnerships.exists()
        # That's a labo
        return self.entity.partnerships_labo.exists()


def children_of_managed_entities():
    """ Returns entity ids whose parents have a ucl management associated """
    from partnership.models import UCLManagementEntity

    cte = EntityVersion.objects.with_children()
    return cte.join(
        UCLManagementEntity, entity_id=cte.col.entity_id,
    ).with_cte(cte).annotate(
        child_entity_id=Func(cte.col.children, function='unnest'),
    ).distinct('child_entity_id').values('child_entity_id')
