from datetime import date

from django.contrib.auth.models import User
from django.db.models import Q
from django.contrib.auth import get_user_model
from base.models.entity_version import EntityVersion

from base.models.person import Person


def user_is_adri(user):
    # FIXME THIS SHOULD BE MOVED TO THE User OR Person MODEL
    try:
        return (
            user
            .person
            .personentity_set
            .filter(Q(entity__entityversion__end_date__gte=date.today())
                    | Q(entity__entityversion__end_date__isnull=True),
                    entity__entityversion__start_date__lte=date.today())
            .filter(entity__entityversion__acronym='ADRI')
            .exists()
        )
    except (Person.DoesNotExist, AttributeError):
        return False


def get_adri_users():
    return get_user_model().objects.filter(
        person__personentity__entity__entityversion__acronym='ADRI'
    )


def get_user_faculties(user):
    return EntityVersion.objects.filter(
        entity_type="FACULTY", entity__entitymanager__person__user=user
    )


def get_adri_emails():
    return get_adri_users().values_list('email', flat=True)


def user_is_gf(user):
    # FIXME THIS SHOULD BE MOVED TO THE User OR Person MODEL
    try:
        return (
            user
            .person
            .entitymanager_set.all()
            .exists()
        )
    except Person.DoesNotExist:
        return False


def user_is_gf_of_faculty(user, faculty):
    if user_is_gf(user):
        return User.objects.filter(pk=user.pk, person__entitymanager__entity=faculty).exists()
    else:
        return False


def user_is_in_user_faculty(user, other_user):
    # FIXME THIS SHOULD BE MOVED TO THE User OR Person MODEL
    try:
        return (
            user
            .person
            .entitymanager_set
            .filter(entity__entitymanager__person__user=other_user)
            .exists()
        )
    except Person.DoesNotExist:
        return False


def merge_date_ranges(ranges):
    """
    Returns an union of date ranges.
    Expects a list of ranges as [{'start': start_date, 'end': end_date},]
    """
    if not ranges:
        return []
    sorted_ranges = sorted(ranges, key=lambda x: x['start'])
    merged_ranges = [sorted_ranges.pop(0)]
    for r in sorted_ranges:
        if merged_ranges[-1]['end'] >= r['start']:
            merged_ranges[-1]['end'] = r['end']
        else:
            merged_ranges.append(r)
    return merged_ranges
