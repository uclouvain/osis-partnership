from datetime import date

from django.db.models import Q

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


def user_is_in_user_faculty(user, other_user):
    # FIXME THIS SHOULD BE MOVED TO THE User OR Person MODEL
    try:
        return (
            user
            .person
            .entitymanager_set
            .filter(entity__entitymanager__person__user=self.author)
            .exists()
        )
    except Person.DoesNotExist:
        return False
