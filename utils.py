from datetime import date

from django.db.models import Q


def user_is_adri(user):
    # FIXME THIS SHOULD BE MOVED TO THE User OR Person MODEL
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