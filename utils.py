from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.db.models import Func, Q

from base.models.entity_version import EntityVersion
from base.models.person import Person


def user_is_adri(user):
    # FIXME THIS SHOULD BE MOVED TO THE User OR Person MODEL
    try:
        return (
            user
            .person
            .partnershipentitymanager_set
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
        person__partnershipentitymanager__entity__entityversion__acronym='ADRI'
    )


def get_user_faculties(user):
    return EntityVersion.objects.filter(
        entity_type="FACULTY", entity__partnershipentitymanager__person__user=user
    )


def get_adri_emails():
    return get_adri_users().values_list('email', flat=True)


def user_is_gf(user):
    # FIXME THIS SHOULD BE MOVED TO THE User OR Person MODEL
    try:
        return (
            user
            .person
            .partnershipentitymanager_set.all()
            .exists()
        )
    except Person.DoesNotExist:
        return False


def user_is_gf_of_faculty(user, entity):
    return User.objects.filter(
        Q(pk=user.pk),
        # entity is a faculty
        Q(person__partnershipentitymanager__entity=entity)
        # entity is a labo
        | Q(person__partnershipentitymanager__entity__parent_of__entity=entity),
    ).exists()


def user_is_in_user_faculty(user, other_user):
    # FIXME THIS SHOULD BE MOVED TO THE User OR Person MODEL
    try:
        return (
            user
            .person
            .partnershipentitymanager_set
            .filter(
                Q(entity__partnershipentitymanager__person__user=other_user)
                | Q(entity__parent_of__entity__partnershipentitymanager__person__user=other_user)
            )
            .exists()
        )
    except Person.DoesNotExist:
        return False


def academic_years(start_academic_year, end_academic_year):
    if start_academic_year is not None or end_academic_year is not None:
        return ' > '.join([
            str(start_academic_year.year) or "N/A",
            str(end_academic_year.year + 1) or "N/A",
        ])
    return "N/A"


def academic_dates(start_academic_date, end_academic_date):
    if start_academic_date is not None or end_academic_date is not None:
        return ' > '.join([
            str(start_academic_date) or "N/A",
            str(end_academic_date) or "N/A",
        ])
    return "N/A"


def merge_agreement_ranges(agreements=None):
    """
    Returns an union of agreements date ranges.
    Expects a list of agreements as [{'start': start_date, 'end': end_date},]
    """
    if agreements is None or len(agreements) == 0:
        return []
    agreements = agreements.copy()
    merged_agreements = [agreements.pop(0)]
    for a in agreements:
        if (merged_agreements[-1]['end'] + 1 >= a['start']
            and merged_agreements[-1]['end'] < a['end']):
            merged_agreements[-1]['end'] = a['end']
        elif merged_agreements[-1]['end'] + 1 < a['start']:
            merged_agreements.append(a)
    return merged_agreements


def children_of_managed_entities():
    from partnership.models import UCLManagementEntity

    """ Returns entity ids whose parents have a ucl management associated """
    cte = EntityVersion.objects.with_children()
    return cte.join(
        UCLManagementEntity, entity_id=cte.col.entity_id,
    ).with_cte(cte).annotate(
        child_entity_id=Func(cte.col.children, function='unnest'),
    ).distinct('child_entity_id').values('child_entity_id')
