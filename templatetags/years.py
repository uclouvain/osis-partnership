from django import template
from partnership.utils import academic_years
register = template.Library()

@register.simple_tag
def years(start_year, end_year):
    return academic_years(start_year, end_year)
