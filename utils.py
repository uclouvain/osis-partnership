from datetime import date

from base.models.person import Person
from django.db.models import Q


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
        return user.person.entitymanager_set.filter(
            entity__entity_version__entity_type="FACULTY"
        ).exists()
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
