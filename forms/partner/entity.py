from django import forms
from django.db.models import Subquery, OuterRef
from django.utils.translation import gettext_lazy as _

from base.models.entity import Entity
from base.models.entity_version_address import EntityVersionAddress
from partnership.models import Contact, PartnerEntity

__all__ = [
    'PartnerEntityForm',
    'PartnerEntityContactForm',
    'EntityVersionAddressForm',
]


class EntityVersionAddressForm(forms.ModelForm):
    class Meta:
        model = EntityVersionAddress
        exclude = ['entity_version', 'location', 'is_main']
        labels = {
            'street_number': _('street_number'),
            'street': _('address'),
            'postal_code': _('postal_code'),
            'state': _('state'),
            'city': _('city'),
            'country': _('country'),
        }


class PartnerEntityContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = [
            'title',
            'last_name',
            'first_name',
            'function',
            'phone',
            'mobile_phone',
            'fax',
            'email',
        ]


class PartnerEntityForm(forms.ModelForm):
    parent = forms.ModelChoiceField(
        label="",
        queryset=Entity.objects.none(),
        required=False,
    )

    class Meta:
        model = PartnerEntity
        exclude = ('entity_version', 'contact_in', 'contact_out')
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': _('name')}),
            'comment': forms.Textarea(attrs={'placeholder': _('comment')}),
        }

    def __init__(self, *args, **kwargs):
        partner = kwargs.pop('partner')
        super().__init__(*args, **kwargs)

        qs = PartnerEntity.objects.filter(
            entity_version__entity__organization__partner=partner,
        )
        qs = Entity.objects.filter(
            entityversion__parent__organization__partner=partner,
        ).annotate(
            name=Subquery(PartnerEntity.objects.filter(
                entity_version__entity=OuterRef('pk'),
            ).values('name')[:1])
        ).distinct('pk')
        if self.instance.pk:
            qs = qs.exclude(
                pk=self.instance.entity_version.entity_id,
            ).exclude(
                # Prevent circle dependency
                entityversion__parent=self.instance.entity_version.entity,
            )
            self.fields['parent'].initial = self.instance.entity_version.parent
        self.fields['parent'].label_from_instance = lambda obj: str(obj.name)
        self.fields['parent'].queryset = qs
