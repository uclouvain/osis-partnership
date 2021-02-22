import re
from itertools import product
from string import ascii_uppercase

from rest_framework.fields import get_attribute as base_get_attribute

from base.models.entity_version import EntityVersion

RE_FIRST_LETTERS = re.compile(r'\b[a-z]', re.IGNORECASE)

def academic_years(start_year, end_year):
    if start_year or end_year:
        start_year = start_year if start_year else "N/A"
        end_year = end_year if end_year else "N/A"
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


def generate_unique_acronym(base_acronym, existing=None):
    if not existing:
        existing = EntityVersion.objects.filter(
            acronym__istartswith=base_acronym
        ).values_list('acronym', flat=True)

    # Else generate the remaining letters
    suffix_length = max(5 - len(base_acronym), 1)
    for suffix in product(ascii_uppercase, repeat=suffix_length):
        if (base_acronym + ''.join(suffix)) not in existing:
            return base_acronym + ''.join(suffix)


def generate_partner_acronym(name, existing=None):
    """
    Return an acronym of minimum 5 uppercase letters beginning by 'X' and first
    letter of each word, following is generataed depending of existing acronyms

    :param name: Title to base the acronym upon
    :param existing: Set if generating a list of acronyms not yet save in DB
    """
    first_letters = ''.join(RE_FIRST_LETTERS.findall(name))
    base_acronym = 'X' + first_letters.upper()

    if not existing:
        existing = EntityVersion.objects.filter(
            acronym__istartswith=base_acronym
        ).values_list('acronym', flat=True)

    # Early return if it satisfies the conditions
    if len(base_acronym) >= 5 and base_acronym not in existing:
        return base_acronym

    # Else generate the remaining letters
    return generate_unique_acronym(base_acronym, existing)
