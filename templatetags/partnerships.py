from django import template
from django.urls import reverse

from partnership import perms

register = template.Library()


@register.filter
def partner_media_download_url(partner, media):
    return reverse('partnerships:partners:medias:download', kwargs={
        'partner_pk': partner.pk,
        'pk': media.pk,
    })


@register.filter
def partnership_media_download_url(partnership, media):
    return reverse('partnerships:medias:download', kwargs={
        'partnership_pk': partnership.pk,
        'pk': media.pk,
    })


@register.filter
def can_change_partner_entity(user, entity):
    return perms.user_can_change_entity(user, entity)


@register.filter
def can_delete_partner_entity(user, entity):
    return perms.user_can_delete_entity(user, entity)


@register.filter
def can_change_agreement(user, agreement):
    return perms.user_can_change_agreement(user, agreement)


@register.filter
def can_delete_agreement(user, agreement):
    return perms.user_can_delete_agreement(user, agreement)


@register.filter
def can_change_management_entity(user, management_entity):
    return perms.user_can_change_ucl_management_entity(user, management_entity)


@register.filter
def can_delete_management_entity(user, management_entity):
    return perms.user_can_delete_ucl_management_entity(user, management_entity)
