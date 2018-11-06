from django import template
from partnership.utils import academic_years as years
from partnership.utils import academic_dates as dates

register = template.Library()

@register.simple_tag
def academic_years(start_year, end_year):
    return years(start_year, end_year)

@register.simple_tag
def academic_dates(start_date, end_date):
    return dates(start_date, end_date)
