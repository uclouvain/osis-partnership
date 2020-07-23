from rest_framework.fields import get_attribute as base_get_attribute


def academic_years(start_year, end_year):
    if start_year or end_year:
        start_year = start_year.year if start_year else "N/A"
        end_year = end_year.year + 1 if end_year else "N/A"
        return '{} > {}'.format(start_year, end_year)
    return "N/A"


def academic_dates(start_date, end_date):
    if start_date or end_date:
        start_date = start_date.strftime('%d/%m/%Y') if start_date else "N/A"
        end_date = end_date.strftime('%d/%m/%Y') if end_date else "N/A"
        return '{} > {}'.format(start_date, end_date)
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


def get_attribute(obj, path, default='', cast_str=True):
    """ Same as getattr but with nested properties """

    try:
        value = base_get_attribute(obj, path.split('.'))
        return default if value is None else (str(value) if cast_str else value)
    except (KeyError, AttributeError):
        return default
