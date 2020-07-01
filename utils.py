from django.contrib.auth import get_user_model

from base.models.entity_version import EntityVersion


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
            start_academic_date.strftime('%d/%m/%Y') or "N/A",
            end_academic_date.strftime('%d/%m/%Y') or "N/A",
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
