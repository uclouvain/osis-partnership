from django import forms
from django.utils.translation import gettext_lazy as _

from base.models.entity_version_address import EntityVersionAddress
from partnership.models import Contact, PartnerEntity

__all__ = ['PartnerEntityForm']


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
        queryset=PartnerEntity.objects.none(),
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
        if self.instance.pk:
            qs = qs.exclude(
                pk=self.instance.pk,
            ).exclude(
                # Prevent circle dependency
                entity_version__parent=self.instance.entity_version.entity,
            )
            self.fields['parent'].initial = self.instance.parent_entity
        self.fields['parent'].queryset = qs
