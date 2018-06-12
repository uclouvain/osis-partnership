from django import forms
from django.utils.translation import ugettext_lazy as _

from base.forms.bootstrap import BootstrapForm
from partnership.models import PartnerType, PartnerTag


class CustomLabelNullBooleanSelect(forms.NullBooleanSelect):

    def __init__(self, attrs=None, empty_label=None):
        if empty_label is None:
            empty_label = _('Unknown')
        choices = (
            ('1', empty_label),
            ('2', _('Yes')),
            ('3', _('No')),
        )
        super(forms.NullBooleanSelect, self).__init__(attrs, choices)


class PartnerFilterForm(BootstrapForm):
    name = forms.CharField(
        label=_('name'),
        widget=forms.TextInput(attrs={'placeholder': _('partner_name')}),
        required=False,
    )
    partner_type = forms.ModelChoiceField(
        label=_('partner_type'),
        queryset=PartnerType.objects.all(),
        empty_label=_('partner_type'),
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
    # city
    # country
    # continent
    is_ies = forms.NullBooleanField(
        label=_('is_ies'),
        widget=CustomLabelNullBooleanSelect(empty_label=_('is_ies')),
        required=False,
    )
    is_valid = forms.NullBooleanField(
        label=_('is_valid'),
        widget=CustomLabelNullBooleanSelect(empty_label=_('is_valid')),
        required=False,
    )
    is_actif = forms.NullBooleanField(
        label=_('is_actif'),
        widget=CustomLabelNullBooleanSelect(empty_label=_('is_actif')),
        required=False,
    )
    tags = forms.ModelMultipleChoiceField(
        label=_('tags'),
        queryset=PartnerTag.objects.all(),
        required = False,
    )
