from dal import autocomplete, forward
from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Func, OuterRef, Q
from django.utils.translation import gettext_lazy as _

from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from base.models.person import Person
from base.utils.cte import CTESubquery
from partnership.models import (
    Partner, Partnership,
    PartnershipEntityManager, children_of_managed_entities,
)
from partnership.utils import user_is_adri
from ..fields import EntityChoiceField, PersonChoiceField

__all__ = ['PartnershipForm']


class PartnershipForm(forms.ModelForm):
    ucl_entity = EntityChoiceField(
        label=_('ucl_entity'),
        queryset=Entity.objects.filter(
            # must have ucl_management
            Q(uclmanagement_entity__isnull=False)
            # or parent must have ucl management
            | Q(pk__in=children_of_managed_entities()),
        ).distinct(),
        widget=autocomplete.ModelSelect2(
            url='partnerships:autocomplete:ucl_entity',
            attrs={
                'class': 'resetting',
                'data-reset': '#id_ucl_university_labo',
            },
        ),
    )

    supervisor = PersonChoiceField(
        label=_('partnership_supervisor'),
        required=False,
        queryset=Person.objects.all(),
        widget=autocomplete.ModelSelect2(
            url='partnerships:autocomplete:person',
            attrs={'data-placeholder': _('same_supervisor_than_management_entity')},
        ),
    )

    class Meta:
        model = Partnership
        fields = (
            'partner',
            'partner_entity',
            'ucl_entity',
            'supervisor',
            'comment',
            'tags',
        )
        widgets = {
            'partner': autocomplete.ModelSelect2(
                url='partnerships:autocomplete:partner',
                attrs={
                    'class': 'resetting',
                    'data-reset': '#id_partner_entity',
                },
            ),
            'partner_entity': autocomplete.ModelSelect2(
                url='partnerships:autocomplete:partner_entity',
                forward=['partner'],
            ),
            'tags': autocomplete.Select2Multiple(),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        field = self.fields['ucl_entity']
        if not user_is_adri(self.user):
            # Get all children entities which have a PartnershipEntityManager
            cte = EntityVersion.objects.with_children(entity_id=OuterRef('pk'))
            qs = cte.join(
                PartnershipEntityManager, entity_id=cte.col.entity_id
            ).with_cte(cte).filter(person=self.user.person).annotate(
                child_entity_id=Func(cte.col.children, function='unnest'),
            )

            # Restrict fields for GF and GS
            field.queryset = field.queryset.filter(
                pk__in=CTESubquery(qs.values('child_entity_id'))
            ).distinct()

            if field.queryset.count() == 1:
                faculty = field.queryset.first()
                if faculty is not None:
                    field.initial = faculty.pk
                field.disabled = True

            if self.instance.pk is not None:
                self.fields['partner'].disabled = True
                field.disabled = True

        try:
            self.fields['partner'].widget.forward.append(
                forward.Const(self.instance.partner.pk, 'partner_pk'),
            )
        except Partner.DoesNotExist:
            pass

    def clean_partner(self):
        partner = self.cleaned_data['partner']
        if self.instance.pk and partner == self.instance.partner:
            return partner
        if not partner.is_actif:
            raise ValidationError(_('partnership_inactif_partner_error'))
        return partner

    def clean(self):
        super().clean()
        partner = self.cleaned_data.get('partner', None)
        partner_entity = self.cleaned_data.get('partner_entity', None)

        if partner_entity and partner_entity.partner != partner:
            self.add_error('partner_entity', _('invalid_partner_entity'))
        return self.cleaned_data
