from dal import autocomplete, forward
from django import forms
from django.utils.translation import gettext_lazy as _

from base.models.person import Person
from partnership.models import UCLManagementEntity
from partnership.utils import user_is_adri
from .fields import PersonChoiceField

__all__ = ['UCLManagementEntityForm']


class UCLManagementEntityForm(forms.ModelForm):
    administrative_responsible = PersonChoiceField(
        label=_('administrative_responsible'),
        queryset=Person.objects.all(),
        widget=autocomplete.ModelSelect2(
            url='partnerships:autocomplete:person',
        ),
    )

    academic_responsible = PersonChoiceField(
        label=_('academic_responsible'),
        queryset=Person.objects.all(),
        widget=autocomplete.ModelSelect2(
            url='partnerships:autocomplete:person',
        ),
    )

    contact_in_person = PersonChoiceField(
        label=_('contact_in_name'),
        queryset=Person.objects.all(),
        required=False,
        widget=autocomplete.ModelSelect2(
            url='partnerships:autocomplete:person',
        ),
    )

    contact_out_person = PersonChoiceField(
        label=_('contact_out_name'),
        queryset=Person.objects.all(),
        required=False,
        widget=autocomplete.ModelSelect2(
            url='partnerships:autocomplete:person',
        ),
    )

    class Meta:
        model = UCLManagementEntity
        fields = [
            'entity',
            'administrative_responsible',
            'academic_responsible',
            'contact_in_person',
            'contact_in_email',
            'contact_in_url',
            'contact_out_person',
            'contact_out_email',
            'contact_out_url',
            'course_catalogue_text_fr',
            'course_catalogue_text_en',
            'course_catalogue_url_fr',
            'course_catalogue_url_en',
        ]
        widgets = {
            'entity': autocomplete.ModelSelect2(
                url='partnerships:autocomplete:faculty_entity',
            ),
            'contact_in_person': autocomplete.ModelSelect2(
                url='partnerships:autocomplete:person',
            ),
            'contact_out_person': autocomplete.ModelSelect2(
                url='partnerships:autocomplete:person',
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        if (self.instance.pk is not None and self.instance.has_linked_partnerships()) or not user_is_adri(self.user):
            self.fields['entity'].disabled = True
        if not user_is_adri(self.user):
            self.fields['academic_responsible'].disabled = True
            self.fields['administrative_responsible'].disabled = True
