from django import forms

from base.models.entity_version import EntityVersion, get_last_version

__all__ = [
    'EducationGroupYearChoiceSelect',
    'EntityChoiceField',
    'EntityChoiceMultipleField',
    'PersonChoiceField',
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
