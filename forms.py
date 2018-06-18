from django import forms
from django.forms import inlineformset_factory
from django.utils.translation import ugettext_lazy as _

from base.forms.bootstrap import BootstrapForm
from partnership.models import PartnerType, PartnerTag, Address, Partner, Media, PartnerEntity, Contact
from reference.models.continent import Continent
from reference.models.country import Country


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


class PartnerForm(BootstrapForm, forms.ModelForm):
    partner_type = forms.ModelChoiceField(
        label=_('partner_type'),
        queryset=PartnerType.objects.all(),
        empty_label=_('partner_type'),
    )

    class Meta:
        model = Partner
        exclude = ['contact_address', 'medias']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': _('partner_name')}),
            'is_valid': forms.CheckboxInput(),
            'start_date': forms.TextInput(attrs={'placeholder': _('start_date')}),
            'end_date': forms.TextInput(attrs={'placeholder': _('end_date')}),
            'partner_code': forms.TextInput(attrs={'placeholder': _('partner_code')}),
            'pic_code': forms.TextInput(attrs={'placeholder': _('pic_code')}),
            'erasmus_code': forms.TextInput(attrs={'placeholder': _('erasmus_code')}),
            'is_ies': forms.CheckboxInput(),
            'is_nonprofit': forms.CheckboxInput(),
            'is_public': forms.CheckboxInput(),
            'use_egracons': forms.CheckboxInput(),
            'type': forms.TextInput(attrs={'placeholder': _('type')}),
            'comment': forms.Textarea(attrs={'placeholder': _('comment')}),
            'phone': forms.TextInput(attrs={'placeholder': _('phone')}),
            'website': forms.URLInput(attrs={'placeholder': _('website')}),
            'email': forms.EmailInput(attrs={'placeholder': _('email')}),
        }


class PartnerEntityForm(BootstrapForm, forms.ModelForm):

    # Address

    address_name = forms.CharField(
        label=_('name'),
        widget=forms.TextInput(attrs={'placeholder': _('address_name_help_text')}),
    )
    address_address = forms.CharField(
        label=_('address'),
        widget=forms.TextInput(attrs={'placeholder': _('address')}),
    )
    address_postal_code = forms.CharField(
        label=_('postal_code'),
        widget=forms.TextInput(attrs={'placeholder': _('postal_code')}),
    )
    address_city = forms.CharField(
        label=_('city'),
        widget=forms.TextInput(attrs={'placeholder': _('city')}),
    )
    address_country = forms.ModelChoiceField(
        label=_('country'),
        queryset=Country.objects.order_by('name'),
        empty_label=_('country'),
    )

    # Contact in

    contact_in_title = forms.ChoiceField(
        label=_('title'),
        choices=Contact.TITLE_CHOICES,
    )

    contact_in_last_name = forms.CharField(
        label=_('last_name'),
        widget=forms.TextInput(attrs={'placeholder': _('last_name')}),
    )

    contact_in_first_name = forms.CharField(
        label=_('first_name'),
        widget=forms.TextInput(attrs={'placeholder': _('first_name')}),
    )
    contact_in_function = forms.CharField(
        label=_('function'),
        widget=forms.TextInput(attrs={'placeholder': _('function')}),
    )

    contact_in_phone = forms.CharField(
        label=_('phone'),
        widget=forms.TextInput(attrs={'placeholder': _('phone')}),
    )

    contact_in_mobile_phone = forms.CharField(
        label=_('mobile_phone'),
        widget=forms.TextInput(attrs={'placeholder': _('address_name_help_text')}),
    )

    contact_in_fax = forms.CharField(
        label=_('fax'),
        widget=forms.TextInput(attrs={'placeholder': _('fax')}),
    )

    contact_in_email = forms.EmailField(
        label=_('email'),
        widget=forms.EmailInput(attrs={'placeholder': _('email')}),
    )

    # Contact out

    contact_out_title = forms.ChoiceField(
        label=_('title'),
        choices=Contact.TITLE_CHOICES,
    )

    contact_out_last_name = forms.CharField(
        label=_('last_name'),
        widget=forms.TextInput(attrs={'placeholder': _('last_name')}),
    )

    contact_out_first_name = forms.CharField(
        label=_('first_name'),
        widget=forms.TextInput(attrs={'placeholder': _('first_name')}),
    )
    contact_out_function = forms.CharField(
        label=_('function'),
        widget=forms.TextInput(attrs={'placeholder': _('function')}),
    )

    contact_out_phone = forms.CharField(
        label=_('phone'),
        widget=forms.TextInput(attrs={'placeholder': _('phone')}),
    )

    contact_out_mobile_phone = forms.CharField(
        label=_('mobile_phone'),
        widget=forms.TextInput(attrs={'placeholder': _('address_name_help_text')}),
    )

    contact_out_fax = forms.CharField(
        label=_('fax'),
        widget=forms.TextInput(attrs={'placeholder': _('fax')}),
    )

    contact_out_email = forms.EmailField(
        label=_('email'),
        widget=forms.EmailInput(attrs={'placeholder': _('email')}),
    )

    class Meta:
        model = PartnerEntity
        exclude = ('address', 'contact_in', 'contact_out')
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': _('name')}),
            'comment': forms.Textarea(attrs={'placeholder': _('comment')}),
        }

    def get_initial_for_field(self, field, field_name):
        value = super(PartnerEntityForm, self).get_initial_for_field(field, field_name)
        if value is None:
            if field_name.startswith('address_'):
                value = getattr(self.instance.address, field_name[len('address_'):], None)
            elif field_name.startswith('contact_in_'):
                value = getattr(self.instance.contact_in, field_name[len('contact_in_'):], None)
            elif field_name.startswith('contact_out_'):
                value = getattr(self.instance.contact_out, field_name[len('contact_out_'):], None)
        return value


PartnerEntitiesFormset = inlineformset_factory(
    Partner,
    PartnerEntity,
    form=PartnerEntityForm,
    extra=1,
)


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
    city = forms.ChoiceField(
        label=_('city'),
        choices=((None, _('city')),),
        required=False,
    )
    country = forms.ModelChoiceField(
        label=_('country'),
        queryset=Country.objects.filter(address__partners__isnull=False).order_by('name'),
        empty_label=_('country'),
        required=False,
    )
    continent = forms.ModelChoiceField(
        label=_('continent'),
        queryset=Continent.objects.filter(country__address__partners__isnull=False).order_by('name'),
        empty_label=_('continent'),
        required=False,
    )
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

    def __init__(self, *args, **kwargs):
        super(PartnerFilterForm, self).__init__(*args, **kwargs)
        cities = (
            Address.objects
                .filter(partners__isnull=False, city__isnull=False)
                .values_list('city', flat=True)
                .order_by('city')
                .distinct('city')
        )
        self.fields['city'].choices = ((None, _('city')),) + tuple((city, city) for city in cities)
