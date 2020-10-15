from django import forms
from django.db.models import Subquery, OuterRef
from django.utils.translation import gettext_lazy as _

from base.forms.widgets import LatLonField
from base.models.entity import Entity
from base.models.entity_version_address import EntityVersionAddress
from partnership.models import Contact, PartnerEntity

__all__ = [
    'PartnerEntityForm',
    'PartnerEntityContactForm',
    'EntityVersionAddressForm',
    'PartnerEntityAddressForm',
]


class EntityVersionAddressForm(forms.ModelForm):
    location = LatLonField()

    def __init__(self, *args, **kwargs):
        # Allow the address to be left out, but still require fields if filled
        kwargs['empty_permitted'] = True
        kwargs['use_required_attribute'] = False
        super().__init__(*args, **kwargs)

    class Meta:
        model = EntityVersionAddress
        exclude = ['entity_version', 'is_main']
        labels = {
            'street_number': _('street_number'),
            'street': _('address'),
            'postal_code': _('postal_code'),
            'state': _('state'),
            'city': _('city'),
            'country': _('country'),
        }


class PartnerEntityAddressForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # Allow the address to be left out, but still require fields if filled
        kwargs['empty_permitted'] = True
        kwargs['use_required_attribute'] = False
        super().__init__(*args, **kwargs)

    class Meta:
        model = EntityVersionAddress
        exclude = ['entity_version', 'is_main', 'location']
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
        exclude = ('entity', 'contact_in', 'contact_out')
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': _('name')}),
            'comment': forms.Textarea(attrs={'placeholder': _('comment')}),
        }

    def __init__(self, *args, **kwargs):
        partner = kwargs.pop('partner')
        super().__init__(*args, **kwargs)

        qs = Entity.objects.filter(
            entityversion__parent__organization__partner=partner,
        ).annotate(
            name=Subquery(PartnerEntity.objects.filter(
                entity=OuterRef('pk'),
            ).values('name')[:1])
        ).distinct('pk')
        if self.instance.pk:
            qs = qs.exclude(
                pk=self.instance.entity_id,
            ).exclude(
                # Prevent circle dependency
                entityversion__parent=self.instance.entity,
            )
            self.fields['parent'].initial = self.instance.entity.most_recent_entity_version.parent
        self.fields['parent'].label_from_instance = lambda obj: str(obj.name)
        self.fields['parent'].queryset = qs
