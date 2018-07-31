from datetime import date

from dal import autocomplete
from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from django.utils.translation import ugettext_lazy as _

from base.forms.utils.datefield import DatePickerInput, DATE_FORMAT
from base.models.academic_year import AcademicYear
from base.models.education_group_year import EducationGroupYear
from base.models.entity import Entity
from base.models.person import Person
from partnership.models import PartnerType, PartnerTag, Address, Partner, Media, PartnerEntity, Contact, PartnershipTag, \
    PartnershipYear, Partnership, PartnershipAgreement, PartnershipConfiguration
from partnership.utils import user_is_adri
from reference.models.continent import Continent
from reference.models.country import Country


class CustomNullBooleanSelect(forms.NullBooleanSelect):

    def __init__(self, attrs=None):
        choices = (
            ('1', '---------'),
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
                attrs={'class': 'datepicker', 'placeholder': _('partner_start_date'), 'autocomplete': 'off'},
            ),
            'end_date': DatePickerInput(
                format=DATE_FORMAT,
                attrs={'class': 'datepicker', 'placeholder': _('partner_end_date'), 'autocomplete': 'off'},
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
            'tags': autocomplete.ModelSelect2Multiple(),
            'now_known_as': autocomplete.ModelSelect2(),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(PartnerForm, self).__init__(*args, **kwargs)
        if not user_is_adri(user):
            del self.fields['is_valid']
            del self.fields['partner_code']
        if self.instance.pk is not None:
            self.fields['now_known_as'].queryset = self.fields['now_known_as'].queryset.exclude(pk=self.instance.pk)
        self.fields['now_known_as'].queryset = self.fields['now_known_as'].queryset.order_by('name')

    def clean(self):
        super(PartnerForm, self).clean()
        if self.cleaned_data['start_date'] and self.cleaned_data['end_date']:
            if self.cleaned_data['start_date'] > self.cleaned_data['end_date']:
                self.add_error('start_date', ValidationError(_('start_date_gt_end_date_error')))

        if not self.cleaned_data['pic_code'] and not self.cleaned_data['is_ies']:
            if not self.cleaned_data['email']:
                self.add_error('email', ValidationError(_('required')))
            if not self.cleaned_data['phone']:
                self.add_error('phone', ValidationError(_('required')))
            if not self.cleaned_data['contact_type']:
                self.add_error('contact_type', ValidationError(_('required')))

        return self.cleaned_data


class PartnerEntityForm(forms.ModelForm):

    """
    This form include fields for related models Address and two Contact.
    """

    # Address

    address_name = forms.CharField(
        label=_('Name'),
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
        label=_('contact_title'),
        choices=((None, '---------'),) + Contact.TITLE_CHOICES,
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
        label=_('contact_title'),
        choices=((None, '---------'),) + Contact.TITLE_CHOICES,
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

    def __init__(self, *args, **kwargs):
        partner = kwargs.pop('partner')
        super(PartnerEntityForm, self).__init__(*args, **kwargs)
        self.fields['parent'].queryset = PartnerEntity.objects.filter(partner=partner).exclude(pk=self.instance.pk)

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


class ContactForm(forms.ModelForm):

    class Meta:
        model = Contact
        fields = [
            'title',
            'type',
            'last_name',
            'first_name',
            'society',
            'function',
            'phone',
            'mobile_phone',
            'fax',
            'email',
            'comment',
        ]


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

    def __init__(self, *args, **kwargs):
        super(PartnerFilterForm, self).__init__(*args, **kwargs)
        cities = (
            Address.objects
            .filter(partners__isnull=False, city__isnull=False)
            .values_list('city', flat=True)
            .order_by('city')
            .distinct('city')
        )
        self.fields['city'].choices = ((None, '---------'),) + tuple((city, city) for city in cities)


class MediaForm(forms.ModelForm):
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
        super(AddressForm, self).__init__(*args, **kwargs)
        self.fields['country'].queryset = Country.objects.all().order_by('name')


class PartnershipFilterForm(forms.Form):

    # UCL

    ucl_university = forms.ModelChoiceField(
        label=_('ucl_university'),
        queryset=Entity.objects.filter(partnerships__isnull=False),
        empty_label=_('ucl_university'),
        required=False,
        widget=autocomplete.ModelSelect2(
            url='partnerships:autocomplete:ucl_university_filter',
            attrs={'data-width': '100%'},
        ),
    )

    ucl_university_labo = forms.ModelChoiceField(
        label=_('ucl_university_labo'),
        queryset=Entity.objects.filter(partnerships_labo__isnull=False),
        empty_label=_('ucl_university_labo_filter'),
        required=False,
        widget=autocomplete.ModelSelect2(
            url='partnerships:autocomplete:ucl_university_labo_filter',
            forward=['ucl_university'],
            attrs={'data-width': '100%'},
        ),
    )

    university_offers = forms.ModelMultipleChoiceField(
        label=_('university_offers'),
        queryset=EducationGroupYear.objects.select_related('academic_year').filter(partnerships__isnull=False).distinct(),
        required=False,
        widget=autocomplete.ModelSelect2Multiple(
            url='partnerships:autocomplete:university_offers_filter',
            forward=['ucl_university_labo'],
            attrs={'data-width': '100%'},
        ),
    )

    # Partner

    partner = forms.ModelChoiceField(
        label=_('partner'),
        queryset=Partner.objects.filter(partnerships__isnull=False).distinct(),
        empty_label=_('partner'),
        widget=autocomplete.ModelSelect2(
            attrs={'data-width': '100%'},
            url='partnerships:autocomplete:partner_partnerships_filter',
        ),
        required=False,
    )
    partner_entity = forms.ModelChoiceField(
        label=_('partner_entity'),
        queryset=PartnerEntity.objects.filter(partnerships__isnull=False).distinct(),
        empty_label=_('partner_entity'),
        widget=autocomplete.ModelSelect2(
            attrs={'data-width': '100%'},
            url='partnerships:autocomplete:partner_entity_partnerships_filter',
            forward=['partner'],
        ),
        required=False,
    )
    partner_type = forms.ModelChoiceField(
        label=_('partner_type'),
        queryset=PartnerType.objects.filter(partners__partnerships__isnull=False).distinct(),
        empty_label=_('partner_type'),
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
        widget=autocomplete.Select2(attrs={'data-width': '100%'}),
        required=False,
    )
    country = forms.ModelChoiceField(
        label=_('country'),

        queryset=(
            Country.objects
                .filter(address__partners__partnerships__isnull=False)
                .order_by('name')
                .distinct()
        ),
        empty_label=_('country'),
        widget=autocomplete.ModelSelect2(attrs={'data-width': '100%'}),
        required=False,
    )
    continent = forms.ModelChoiceField(
        label=_('continent'),
        queryset=(
            Continent.objects
                .filter(country__address__partners__partnerships__isnull=False)
                .order_by('name')
                .distinct()
        ),
        empty_label=_('continent'),
        required=False,
    )
    partner_tags = forms.ModelMultipleChoiceField(
        label=_('tags'),
        queryset=PartnerTag.objects.filter(partners__partnerships__isnull=False).distinct(),
        widget=autocomplete.ModelSelect2Multiple(attrs={'data-width': '100%'}),
        required=False,
    )

    # Partnerships

    education_field = forms.ChoiceField(
        label=_('education_field'),
        choices=((None, '---------'),) + PartnershipYear.EDUCATION_FIELD_CHOICES,
        widget=autocomplete.Select2(attrs={'data-width': '100%'}),
        required=False,
    )
    education_level = forms.ChoiceField(
        label=_('education_level'),
        choices=((None, '---------'),) + PartnershipYear.EDUCATION_LEVEL_CHOICES,
        required=False,
    )
    is_sms = forms.NullBooleanField(
        label=_('is_sms'),
        widget=CustomNullBooleanSelect(),
        required=False,
    )
    is_smp = forms.NullBooleanField(
        label=_('is_smp'),
        widget=CustomNullBooleanSelect(),
        required=False,
    )
    is_sta = forms.NullBooleanField(
        label=_('is_sta'),
        widget=CustomNullBooleanSelect(),
        required=False,
    )
    is_stt = forms.NullBooleanField(
        label=_('is_stt'),
        widget=CustomNullBooleanSelect(),
        required=False,
    )
    partnership_type = forms.ChoiceField(
        label=_('partnership_type'),
        choices=((None, '---------'),) + PartnershipYear.TYPE_CHOICES,
        required=False,
    )
    supervisor = forms.ModelChoiceField(
        label=_('partnership_supervisor'),
        queryset=Person.objects.filter(partnerships_supervisor__isnull=False),
        widget=autocomplete.ModelSelect2(attrs={'data-width': '100%'}),
        required=False,
    )
    tags = forms.ModelMultipleChoiceField(
        label=_('tags'),
        queryset=PartnershipTag.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(attrs={'data-width': '100%'}),
        required=False,
    )

    partnership_in = forms.ModelChoiceField(
        label=_('partnership_in'),
        queryset=AcademicYear.objects.all(),
        required=False,
    )
    partnership_ending_in = forms.ModelChoiceField(
        label=_('partnership_ending_in'),
        queryset=AcademicYear.objects.all(),
        required=False,
    )
    partnership_valid_in = forms.ModelChoiceField(
        label=_('partnership_valid_in'),
        queryset=AcademicYear.objects.all(),
        required=False,
    )
    partnership_not_valid_in = forms.ModelChoiceField(
        label=_('partnership_not_valid_in'),
        queryset=AcademicYear.objects.all(),
        required=False,
    )
    comment = forms.CharField(
        label=_('comment'),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super(PartnershipFilterForm, self).__init__(*args, **kwargs)
        cities = (
            Address.objects
            .filter(partners__partnerships__isnull=False, city__isnull=False)
            .values_list('city', flat=True)
            .order_by('city')
            .distinct('city')
        )
        self.fields['city'].choices = ((None, _('city')),) + tuple((city, city) for city in cities)


class PartnershipForm(forms.ModelForm):

    class Meta:
        model = Partnership
        fields = (
            'start_date',
            'supervisor',
            'partner',
            'partner_entity',
            'ucl_university',
            'ucl_university_labo',
            'university_offers',
            'comment',
            'tags',
        )
        widgets = {
            'start_date': DatePickerInput(
                format=DATE_FORMAT,
                attrs={'class': 'datepicker', 'autocomplete': 'off'},
            ),
            'supervisor': autocomplete.ModelSelect2(
                url='partnerships:autocomplete:person',
            ),
            'ucl_university': autocomplete.ModelSelect2(
                url='partnerships:autocomplete:ucl_university',
                attrs={
                    'class': 'resetting',
                    'data-reset': '#id_ucl_university_labo, #id_university_offers',
                },
            ),
            'ucl_university_labo': autocomplete.ModelSelect2(
                url='partnerships:autocomplete:ucl_university_labo',
                forward=['ucl_university'],
                attrs={
                    'class': 'resetting',
                    'data-reset': '#id_university_offers',
                },
            ),
            'university_offers': autocomplete.ModelSelect2Multiple(
                url='partnerships:autocomplete:university_offers',
                forward=['ucl_university_labo'],
            ),
            'tags': autocomplete.Select2Multiple(),
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
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(PartnershipForm, self).__init__(*args, **kwargs)

    def clean_start_date(self):
        start_date = self.cleaned_data['start_date']
        # Check for agreements
        if self.instance.agreements.filter(start_academic_year__year__lt=start_date.year).exists():
            raise ValidationError(_('partnership_start_date_after_agreement_error'))
        if user_is_adri(self.user):
            return start_date
        if self.instance.pk is not None and self.instance.start_date == start_date:
            return start_date
        # GF User can create if before year N - 1 and the day/month specified in the configuration.
        today = date.today()
        configuration = PartnershipConfiguration.get_configuration()
        min_date = date(
            today.year,
            configuration.partnership_creation_max_date_month,
            configuration.partnership_creation_max_date_day
        )
        if start_date.year == today.year or start_date <= min_date:
            raise ValidationError(_('partnership_start_date_gf_too_late'))
        return start_date


class PartnershipYearForm(forms.ModelForm):

    class Meta:
        model = PartnershipYear
        fields = (
            'academic_year',
            'education_field',
            'education_level',
            'is_sms',
            'is_smp',
            'is_sta',
            'is_stt',
            'partnership_type',
        )
        widgets = {
            'education_field': autocomplete.Select2(),
        }


PartnershipYearInlineFormset = inlineformset_factory(
    Partnership,
    PartnershipYear,
    form=PartnershipYearForm,
)


class PartnershipAgreementForm(forms.ModelForm):

    class Meta:
        model = PartnershipAgreement
        fields = [
            'start_academic_year',
            'end_academic_year',
            'status',
            'eligible',
            'comment',
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(PartnershipAgreementForm, self).__init__(*args, **kwargs)
        if not user_is_adri(user):
            del self.fields['status']
            del self.fields['eligible']

    def clean(self):
        super(PartnershipAgreementForm, self).clean()
        if self.cleaned_data['start_academic_year'].year > self.cleaned_data['end_academic_year'].year:
            self.add_error('start_academic_year', ValidationError(_('start_date_after_end_date')))
            self.add_error('end_academic_year', ValidationError(_('start_date_after_end_date')))
        return self.cleaned_data


class PartnershipConfigurationForm(forms.ModelForm):

    class Meta:
        model = PartnershipConfiguration
        fields = [
            'partnership_creation_max_date_day',
            'partnership_creation_max_date_month',
            'partnership_update_max_date_day',
            'partnership_update_max_date_month',
        ]

    def clean(self):
        super(PartnershipConfigurationForm, self).clean()
        try:
            date(
                2001,
                self.cleaned_data['partnership_creation_max_date_month'],
                self.cleaned_data['partnership_creation_max_date_day'],
            )
        except ValueError:
            self.add_error(
                'partnership_creation_max_date_day',
                ValidationError(_('invalid_partnership_creation_max_date'))
            )

        try:
            date(
                2001,
                self.cleaned_data['partnership_update_max_date_month'],
                self.cleaned_data['partnership_update_max_date_day'],
            )
        except ValueError:
            self.add_error(
                'partnership_update_max_date_day',
                ValidationError(_('invalid_partnership_update_max_date'))
            )
        return self.cleaned_data
