from dal import autocomplete, forward
from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from base.models.entity import Entity
from base.models.person import Person
from partnership.models import (
    Partner, Partnership,
    children_of_managed_entities,
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
        ),
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
        if self.user is not None:
            if not user_is_adri(self.user):

                # Restrict fields for GF
                # FIXME hierarchy not flat
                self.fields['ucl_entity'].queryset = self.fields['ucl_entity'].queryset.filter(
                    Q(partnershipentitymanager__person=self.user.person)
                    | Q(entityversion__parent__partnershipentitymanager__person=self.user.person)
                    | Q(entityversion__parent__entityversion__parent__partnershipentitymanager__person=self.user.person),
                ).distinct()

                if self.fields['ucl_entity'].queryset.count() == 1:
                    faculty = self.fields['ucl_entity'].queryset.first()
                    if faculty is not None:
                        self.fields['ucl_entity'].initial = faculty.pk
                    self.fields['ucl_entity'].disabled = True

                if self.instance.pk is not None:
                    self.fields['partner'].disabled = True
                    self.fields['ucl_entity'].disabled = True
            else:
                self.fields['ucl_entity'].queryset = self.fields['ucl_entity'].queryset.distinct()
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
