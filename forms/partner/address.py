from dal import autocomplete
from django import forms
from django.utils.translation import gettext_lazy as _

from partnership.models import Address
from reference.models.country import Country

__all__ = ['AddressForm']


class AddressForm(forms.ModelForm):
    # FIXME Move with Address model to a more generic app

    class Meta:
        model = Address
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': _('address_name_help_text')}),
            'address': forms.Textarea(attrs={'placeholder': _('address')}),
            'postal_code': forms.TextInput(attrs={'placeholder': _('postal_code')}),
            'city': forms.TextInput(attrs={'placeholder': _('city')}),
            'country': autocomplete.ModelSelect2(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['country'].queryset = Country.objects.all().order_by('name')
