from django.utils.translation import gettext_lazy as _
from django_cte.query import CTECompiler

default_app_config = 'partnership.apps.PartnershipConfig'

# Only used to add the strings in the po files
_('partnerships_general_configuration')
_('partnerships_financing_configuration')

# TODO remove this monkeypatch once either django-cte has fixed this or Django is upgraded > 3.1.14
# see https://github.com/dimagi/django-cte/issues/26
# fixed in https://code.djangoproject.com/ticket/31002
orginal_generate_sql = CTECompiler.generate_sql


def generate_sql(cls, connection, query, as_sql):
    ret = orginal_generate_sql(connection, query, as_sql)
    # We need to cast the second part of the return value if it's a tuple
    if len(ret) == 2 and isinstance(ret[1], tuple):
        return ret[0], list(ret[1])


CTECompiler.generate_sql = classmethod(generate_sql)
