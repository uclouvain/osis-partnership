from django import forms
from django.utils.translation import ugettext_lazy as _

from partnerships.models import PartnerType, PartnerTag


class PartnerFilterForm(forms.Form):
    name = forms.CharField(label=_('name'), required=False)
    partner_type = forms.ModelChoiceField(
        label=_('partner_type'),
        queryset=PartnerType.objects.all(),
        required=False,
    )
    pic_code = forms.CharField(label=_('pic_code'), required=False)
    # city
    # country
    # continent
    is_ies = forms.NullBooleanField(label=_('is_ies'), required=False)
    is_valid = forms.NullBooleanField(label=_('is_valid'), required=False)
    is_actif = forms.NullBooleanField(label=_('is_actif'), required=False)
    tags = forms.ModelMultipleChoiceField(
        label=_('tags'),
        queryset=PartnerTag.objects.all(),
        required = False,
    )
