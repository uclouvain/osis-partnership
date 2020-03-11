from dal import autocomplete
from django import forms
from django.utils.translation import gettext_lazy as _

from partnership.models import Address, PartnerTag, PartnerType
from reference.models.continent import Continent
from reference.models.country import Country
from ..widgets import CustomNullBooleanSelect

__all__ = ['PartnerFilterForm']


class PartnerFilterForm(forms.Form):
    name = forms.CharField(
        label=_('Name'),
        widget=forms.TextInput(attrs={'placeholder': _('partner_name')}),
        required=False,
    )
    partner_type = forms.ModelChoiceField(
        label=_('partner_type'),
        queryset=PartnerType.objects.all(),
        required=False,
    )
    pic_code = forms.CharField(
        label=_('pic_code'),
        widget=forms.TextInput(attrs={'placeholder': _('pic_code')}),
        required=False,
    )
    erasmus_code = forms.CharField(
        label=_('erasmus_code'),
        widget=forms.TextInput(attrs={'placeholder': _('erasmus_code')}),
        required=False,
    )
    city = forms.ChoiceField(
        label=_('city'),
        choices=((None, '---------'),),
        widget=autocomplete.Select2(attrs={'data-width': '100%'}),
        required=False,
    )
    country = forms.ModelChoiceField(
        label=_('country'),
        queryset=Country.objects.filter(address__partners__isnull=False).order_by('name').distinct(),
        widget=autocomplete.ModelSelect2(attrs={'data-width': '100%'}),
        required=False,
    )
    continent = forms.ModelChoiceField(
        label=_('continent'),
        queryset=Continent.objects.filter(country__address__partners__isnull=False).order_by('name').distinct(),
        required=False,
    )
    is_ies = forms.NullBooleanField(
        label=_('is_ies'),
        required=False,
        widget=CustomNullBooleanSelect(),
    )
    is_valid = forms.NullBooleanField(
        label=_('is_valid'),
        required=False,
        widget=CustomNullBooleanSelect(),
    )
    is_actif = forms.NullBooleanField(
        label=_('is_actif'),
        required=False,
        widget=CustomNullBooleanSelect(),
    )
    tags = forms.ModelMultipleChoiceField(
        label=_('tags'),
        queryset=PartnerTag.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(attrs={'data-width': '100%'}),
        required=False,
    )
    ordering = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cities = (
            Address.objects
            .filter(partners__isnull=False, city__isnull=False)
            .values_list('city', flat=True)
            .order_by('city')
            .distinct('city')
        )
        self.fields['city'].choices = ((None, '---------'),) + tuple((city, city) for city in cities)

    def clean_ordering(self):
        # Django filters expects a list
        ordering = self.cleaned_data.get('ordering')
        if ordering:
            return [ordering]
