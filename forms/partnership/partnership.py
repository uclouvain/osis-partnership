from dal import autocomplete, forward
from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from base.models.entity import Entity
from base.models.enums.entity_type import FACULTY
from base.models.person import Person
from partnership.models import (
    Partner, Partnership,
    children_of_managed_entities,
)
from partnership.utils import user_is_adri
from ..fields import EntityChoiceField, PersonChoiceField

__all__ = ['PartnershipForm']


class PartnershipForm(forms.ModelForm):
    ucl_university = EntityChoiceField(
        label=_('ucl_university'),
        queryset=Entity.objects.filter(
            # must be faculty
            Q(entityversion__entity_type=FACULTY),
            # and have ucl management, or labos having ucl management
            Q(uclmanagement_entity__isnull=False)
            | Q(parent_of__entity__uclmanagement_entity__isnull=False),
        ),
        widget=autocomplete.ModelSelect2(
            url='partnerships:autocomplete:ucl_university',
            attrs={
                'class': 'resetting',
                'data-reset': '#id_ucl_university_labo',
            },
        ),
    )

    ucl_university_labo = EntityChoiceField(
        label=_('ucl_university_labo'),
        queryset=Entity.objects.filter(
            # must have ucl_management
            uclmanagement_entity__isnull=False,
            # or parent must have ucl management
            pk__in=children_of_managed_entities(),
        ).distinct(),
        widget=autocomplete.ModelSelect2(
            url='partnerships:autocomplete:ucl_university_labo',
            forward=['ucl_university'],
        ),
        required=False,
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
            'ucl_university',
            'ucl_university_labo',
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
                self.fields['ucl_university'].queryset = self.fields['ucl_university'].queryset.filter(
                    Q(partnershipentitymanager__person__user=self.user)
                    | Q(entityversion__parent__partnershipentitymanager__person__user=self.user),
                ).distinct()

                if self.fields['ucl_university'].queryset.count() == 1:
                    faculty = self.fields['ucl_university'].queryset.first()
                    if faculty is not None:
                        self.fields['ucl_university'].initial = faculty.pk
                    self.fields['ucl_university'].disabled = True

                if self.instance.pk is not None:
                    self.fields['partner'].disabled = True
                    self.fields['ucl_university_labo'].disabled = True
                    self.fields['ucl_university'].disabled = True
            else:
                self.fields['ucl_university'].queryset = self.fields['ucl_university'].queryset.distinct()
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
        ucl_university = self.cleaned_data.get('ucl_university', None)
        ucl_university_labo = self.cleaned_data.get('ucl_university_labo', None)

        if partner_entity and partner_entity.partner != partner:
            self.add_error('partner_entity', _('invalid_partner_entity'))

        if (
            ucl_university_labo
            and not ucl_university_labo.entityversion_set.filter(parent=ucl_university).exists()
        ):
            self.add_error('ucl_university_labo', _('invalid_ucl_university_labo'))
        return self.cleaned_data
