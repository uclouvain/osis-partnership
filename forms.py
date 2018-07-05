from django.core.exceptions import ValidationError

from base.forms.bootstrap import BootstrapForm, BootstrapModelForm
from base.forms.utils.datefield import DATE_FORMAT, DatePickerInput
from base.models.entity_version import EntityVersion
from django import forms
from django.utils.translation import ugettext_lazy as _

from base.forms.bootstrap import BootstrapForm
from base.forms.utils.datefield import DatePickerInput, DATE_FORMAT
from base.models.education_group_year import EducationGroupYear
from partnership.models import PartnerType, PartnerTag, Address, Partner, Media, PartnerEntity, Contact, ContactType, \
    Partnership, PartnershipTag, PartnershipType, PartnershipYear
from partnership.utils import user_is_adri
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


class PartnerForm(forms.ModelForm):
    class Meta:
        model = Partner
        exclude = ['contact_address', 'medias']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': _('partner_name')}),
            'is_valid': forms.CheckboxInput(),
            'start_date': DatePickerInput(
                format=DATE_FORMAT,
                attrs={'class': 'datepicker', 'placeholder': _('start_date')},
            ),
            'end_date': DatePickerInput(
                format=DATE_FORMAT,
                attrs={'class': 'datepicker', 'placeholder': _('end_date')},
            ),
            'partner_code': forms.TextInput(attrs={'placeholder': _('partner_code')}),
            'pic_code': forms.TextInput(attrs={'placeholder': _('pic_code')}),
            'erasmus_code': forms.TextInput(attrs={'placeholder': _('erasmus_code')}),
            'is_ies': forms.CheckboxInput(),
            'is_nonprofit': forms.CheckboxInput(),
            'is_public': forms.CheckboxInput(),
            'use_egracons': forms.CheckboxInput(),
            'comment': forms.Textarea(attrs={'placeholder': _('comment')}),
            'phone': forms.TextInput(attrs={'placeholder': _('phone')}),
            'website': forms.URLInput(attrs={'placeholder': _('website')}),
            'email': forms.EmailInput(attrs={'placeholder': _('email')}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(PartnerForm, self).__init__(*args, **kwargs)
        if not user_is_adri(user):
            del self.fields['is_valid']

    def clean(self):
        super(PartnerForm, self).clean()
        if self.cleaned_data['start_date'] and self.cleaned_data['end_date']:
            if self.cleaned_data['start_date'] > self.cleaned_data['end_date']:
                self.add_error('start_date', ValidationError(_('start_date_gt_end_date_error')))

        if not self.cleaned_data['pic_code'] and not self.cleaned_data['is_ies']:
            if not self.cleaned_data['email']:
                self.add_error('email', ValidationError(_('mandatory_if_not_pic_ies')))
            if not self.cleaned_data['phone']:
                self.add_error('phone', ValidationError(_('mandatory_if_not_pic_ies')))
            if not self.cleaned_data['contact_type']:
                self.add_error('contact_type', ValidationError(_('mandatory_if_not_pic_ies')))

        return self.cleaned_data


class PartnerEntityForm(BootstrapForm, forms.ModelForm):
    """
    This form include fields for related models Address and two Contact.
    """

    # Address

    address_name = forms.CharField(
        label=_('name'),
        widget=forms.TextInput(attrs={'placeholder': _('address_name_help_text')}),
        required=False,
    )
    address_address = forms.CharField(
        label=_('address'),
        widget=forms.TextInput(attrs={'placeholder': _('address')}),
        required=False,
    )
    address_postal_code = forms.CharField(
        label=_('postal_code'),
        widget=forms.TextInput(attrs={'placeholder': _('postal_code')}),
        required=False,
    )
    address_city = forms.CharField(
        label=_('city'),
        widget=forms.TextInput(attrs={'placeholder': _('city')}),
        required=False,
    )
    address_country = forms.ModelChoiceField(
        label=_('country'),
        queryset=Country.objects.order_by('name'),
        empty_label=_('country'),
        required=False,
    )

    # Contact in

    contact_in_title = forms.ChoiceField(
        label=_('title'),
        choices=Contact.TITLE_CHOICES,
        initial=Contact.TITLE_MISTER,
        required=False,
    )

    contact_in_last_name = forms.CharField(
        label=_('last_name'),
        widget=forms.TextInput(attrs={'placeholder': _('last_name')}),
        required=False,
    )

    contact_in_first_name = forms.CharField(
        label=_('first_name'),
        widget=forms.TextInput(attrs={'placeholder': _('first_name')}),
        required=False,
    )

    contact_in_function = forms.CharField(
        label=_('function'),
        widget=forms.TextInput(attrs={'placeholder': _('function')}),
        required=False,
    )

    contact_in_phone = forms.CharField(
        label=_('phone'),
        widget=forms.TextInput(attrs={'placeholder': _('phone')}),
        required=False,
    )

    contact_in_mobile_phone = forms.CharField(
        label=_('mobile_phone'),
        widget=forms.TextInput(attrs={'placeholder': _('mobile_phone')}),
        required=False,
    )

    contact_in_fax = forms.CharField(
        label=_('fax'),
        widget=forms.TextInput(attrs={'placeholder': _('fax')}),
        required=False,
    )

    contact_in_email = forms.EmailField(
        label=_('email'),
        widget=forms.EmailInput(attrs={'placeholder': _('email')}),
        required=False,
    )

    # Contact out

    contact_out_title = forms.ChoiceField(
        label=_('title'),
        choices=Contact.TITLE_CHOICES,
        initial=Contact.TITLE_MISTER,
        required=False,
    )

    contact_out_last_name = forms.CharField(
        label=_('last_name'),
        widget=forms.TextInput(attrs={'placeholder': _('last_name')}),
        required=False,
    )

    contact_out_first_name = forms.CharField(
        label=_('first_name'),
        widget=forms.TextInput(attrs={'placeholder': _('first_name')}),
        required=False,
    )

    contact_out_function = forms.CharField(
        label=_('function'),
        widget=forms.TextInput(attrs={'placeholder': _('function')}),
        required=False,
    )

    contact_out_phone = forms.CharField(
        label=_('phone'),
        widget=forms.TextInput(attrs={'placeholder': _('phone')}),
        required=False,
    )

    contact_out_mobile_phone = forms.CharField(
        label=_('mobile_phone'),
        widget=forms.TextInput(attrs={'placeholder': _('mobile_phone')}),
        required=False,
    )

    contact_out_fax = forms.CharField(
        label=_('fax'),
        widget=forms.TextInput(attrs={'placeholder': _('fax')}),
        required=False,
    )

    contact_out_email = forms.EmailField(
        label=_('email'),
        widget=forms.EmailInput(attrs={'placeholder': _('email')}),
        required=False,
    )

    class Meta:
        model = PartnerEntity
        exclude = ('partner', 'address', 'contact_in', 'contact_out')
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': _('name')}),
            'comment': forms.Textarea(attrs={'placeholder': _('comment')}),
        }

    def get_initial_for_field(self, field, field_name):
        """ Set value of foreign keys fields """
        value = super(PartnerEntityForm, self).get_initial_for_field(field, field_name)
        if value is None:
            if field_name.startswith('address_'):
                value = getattr(self.instance.address, field_name[len('address_'):], None)
            elif field_name.startswith('contact_in_'):
                value = getattr(self.instance.contact_in, field_name[len('contact_in_'):], None)
            elif field_name.startswith('contact_out_'):
                value = getattr(self.instance.contact_out, field_name[len('contact_out_'):], None)
        return value

    def save_address(self, partner_entity, commit=True):
        if partner_entity.address is None:
            partner_entity.address = Address()
        address = partner_entity.address
        address.name = self.cleaned_data['address_name']
        address.address = self.cleaned_data['address_address']
        address.postal_code = self.cleaned_data['address_postal_code']
        address.city = self.cleaned_data['address_city']
        address.country = self.cleaned_data['address_country']
        if commit:
            address.save()
            partner_entity.address_id = address.id
        return address

    def save_contact_in(self, partner_entity, commit=True):
        if partner_entity.contact_in is None:
            partner_entity.contact_in = Contact()
        contact_in = partner_entity.contact_in
        contact_in.title = self.cleaned_data['contact_in_title']
        contact_in.last_name = self.cleaned_data['contact_in_last_name']
        contact_in.first_name = self.cleaned_data['contact_in_first_name']
        contact_in.function = self.cleaned_data['contact_in_function']
        contact_in.phone = self.cleaned_data['contact_in_phone']
        contact_in.mobile_phone = self.cleaned_data['contact_in_mobile_phone']
        contact_in.fax = self.cleaned_data['contact_in_fax']
        contact_in.email = self.cleaned_data['contact_in_email']
        if commit:
            contact_in.save()
            partner_entity.contact_in_id = contact_in.id
        return contact_in

    def save_contact_out(self, partner_entity, commit=True):
        if partner_entity.contact_out is None:
            partner_entity.contact_out = Contact()
        contact_out = partner_entity.contact_out
        contact_out.title = self.cleaned_data['contact_out_title']
        contact_out.last_name = self.cleaned_data['contact_out_last_name']
        contact_out.first_name = self.cleaned_data['contact_out_first_name']
        contact_out.function = self.cleaned_data['contact_out_function']
        contact_out.phone = self.cleaned_data['contact_out_phone']
        contact_out.mobile_phone = self.cleaned_data['contact_out_mobile_phone']
        contact_out.fax = self.cleaned_data['contact_out_fax']
        contact_out.email = self.cleaned_data['contact_out_email']
        if commit:
            contact_out.save()
            partner_entity.contact_out_id = contact_out.id
        return contact_out

    def save(self, commit=True):
        partner_entity = super(PartnerEntityForm, self).save(commit=False)
        self.save_address(partner_entity, commit=commit)
        self.save_contact_in(partner_entity, commit=commit)
        self.save_contact_out(partner_entity, commit=commit)
        if commit:
            partner_entity.save()
            self.save_m2m()
        return partner_entity


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
        required=False,
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


class MediaForm(BootstrapForm, forms.ModelForm):
    # FIXME Move with Media model to a more generic app

    class Meta:
        model = Media
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': _('name')}),
            'description': forms.Textarea(attrs={'placeholder': _('description')}),
            'url': forms.URLInput(attrs={'placeholder': _('url')}),
        }

    def clean(self):
        super(MediaForm, self).clean()
        file = self.cleaned_data.get('file', None)
        url = self.cleaned_data.get('url', None)
        if file and url:
            raise forms.ValidationError(_('file_or_url_only'))
        if not file and not url:
            raise forms.ValidationError(_('file_or_url_required'))
        return self.cleaned_data


class AddressForm(BootstrapForm, forms.ModelForm):
    # FIXME Move with Address model to a more generic app

    class Meta:
        model = Address
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': _('address_name_help_text')}),
            'address': forms.Textarea(attrs={'placeholder': _('address')}),
            'postal_code': forms.TextInput(attrs={'placeholder': _('postal_code')}),
            'city': forms.TextInput(attrs={'placeholder': _('city')}),
        }

    def __init__(self, *args, **kwargs):
        super(AddressForm, self).__init__(*args, **kwargs)
        self.fields['country'].queryset = Country.objects.all().order_by('name')


class PartnershipFilterForm(forms.Form):

    # UCL

    ucl_university = forms.ModelChoiceField(
        label=_('ucl_university'),
        queryset=EntityVersion.objects.filter(partnerships__isnull=False),\
        empty_label=_('ucl_university'),
        required=False,
    )

    ucl_university_labo = forms.ModelChoiceField(
        label=_('ucl_university_labo'),
        queryset=EntityVersion.objects.filter(partnerships_labo__isnull=False),
        empty_label=_('ucl_university_labo'),
        required=False,
    )

    university_offers = forms.ModelChoiceField(
        label=_('university_offers'),
        queryset=EducationGroupYear.objects.select_related('academic_year').filter(partnerships__isnull=False),
        empty_label=_('university_offers'),
        required=False,
    )

    # Partner

    partner = forms.ModelChoiceField(
        label=_('partner'),
        queryset=Partner.objects.filter(partnerships__isnull=False),
        empty_label=_('partner'),
        required=False,
    )
    partner_entity = forms.ModelChoiceField(
        label=_('partner_entity'),
        queryset=PartnerEntity.objects.filter(partner__partnerships__isnull=False),
        empty_label=_('partner_entity'),
        required=False,
    )
    partner_type = forms.ModelChoiceField(
        label=_('partner_type'),
        queryset=PartnerType.objects.filter(partners__partnerships__isnull=False),
        empty_label=_('partner_type'),
        required=False,
    )
    city = forms.ChoiceField(
        label=_('city'),
        choices=((None, _('city')),),
        required=False,
    )
    country = forms.ModelChoiceField(
        label=_('country'),

        queryset=(
            Country.objects
                .filter(address__partners__partnerships__isnull=False)
                .order_by('name')
        ),
        empty_label=_('country'),
        required=False,
    )
    continent = forms.ModelChoiceField(
        label=_('continent'),
        queryset=(
            Continent.objects
                .filter(country__address__partners__partnerships__isnull=False)
                .order_by('name')
        ),
        empty_label=_('continent'),
        required=False,
    )
    partner_tags = forms.ModelMultipleChoiceField(
        label=_('tags'),
        queryset=PartnerTag.objects.filter(partners__partnerships__isnull=False),
        required=False,
    )

    # Partnerships

    mobility_type = forms.ChoiceField(
        label=_('mobility_type'),
        choices=((None, _('mobility_type')),),
        required=False,
    )
    partnership_type = forms.ModelChoiceField(
        label=_('partnership_type'),
        queryset=PartnershipType.objects.all(),
        empty_label=_('partnership_type'),
        required=False,
    )
    tags = forms.ModelMultipleChoiceField(
        label=_('tags'),
        queryset=PartnershipTag.objects.all(),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super(PartnershipFilterForm, self).__init__(*args, **kwargs)
        cities = (
            Address.objects
            .filter(partners__isnull=False, city__isnull=False)
            .values_list('city', flat=True)
            .order_by('city')
            .distinct('city')
        )
        self.fields['city'].choices = ((None, _('city')),) + tuple((city, city) for city in cities)

        mobility_types = (
            PartnershipYear.objects
                .values_list('mobility_type', flat=True)
                .order_by('mobility_type')
                .distinct('mobility_type')
        )
        mobility_types = tuple((mobility_type, mobility_type) for mobility_type in mobility_types)
        self.fields['mobility_type'].choices = ((None, _('mobility_type')),) + mobility_types
