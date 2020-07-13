from dal import autocomplete
from dal_contenttypes.fields import GenericModelMixin
from django import forms
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist

from base.models.entity_version import EntityVersion, get_last_version

__all__ = [
    'EducationGroupYearChoiceSelect',
    'EntityChoiceField',
    'EntityChoiceMultipleField',
    'PersonChoiceField',
    'FundingChoiceField',
]


class EducationGroupYearChoiceSelect(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return '{0} - {1}'.format(obj.acronym, obj.title)


class EntityChoiceFieldMixin(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        try:
            entity_version = get_last_version(obj)
            return '{0} - {1}'.format(entity_version.acronym, entity_version.title)
        except EntityVersion.DoesNotExist:
            return str(obj)


class EntityChoiceField(EntityChoiceFieldMixin, forms.ModelChoiceField):
    pass


class EntityChoiceMultipleField(EntityChoiceFieldMixin, forms.ModelMultipleChoiceField):
    pass


class PersonChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, person):
        return '{0} - {1}'.format(person, person.email)


class FundingListSelect2(autocomplete.ListSelect2):
    def filter_choices_to_render(self, selected_choices):
        """Replace self.choices with selected_choices."""
        if selected_choices:
            try:
                model_name, object_id = selected_choices[0].split('-')
                model = apps.get_model('partnership', model_name)

                self.choices = [
                    (selected_choices[0], str(model.objects.get(pk=object_id)))
                ]
            except (ValueError, ObjectDoesNotExist):
                self.choices = []


class FundingChoiceField(GenericModelMixin, forms.ModelChoiceField):
    """Replacement for ModelChoiceField supporting multiple model choices."""
    def __init__(self, *args, **kwargs):
        super().__init__(
            queryset=ContentType.objects.none(),
            widget=FundingListSelect2(
                url='partnerships:autocomplete:funding',
            ),
            *args,
            **kwargs
        )

    def to_python(self, value):
        """ Given a value like 'fundingtype-5', return the matching instance """
        if not value:
            return value

        try:
            model_name, object_id = value.split('-')
            model = apps.get_model('partnership', model_name)
            return model.objects.get(pk=object_id)
        except (ValueError, ObjectDoesNotExist):
            raise forms.ValidationError(
                self.error_messages['invalid_choice'],
                code='invalid_choice',
            )

    def prepare_value(self, value):
        if hasattr(value, '_meta'):
            return '%s-%s' % (
                ContentType.objects.get_for_model(value).model, value.pk
            )
        return super().prepare_value(value)
