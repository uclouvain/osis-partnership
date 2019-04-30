from django import template
from django.urls import reverse

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
    return entity.user_can_change(user)


@register.filter
def can_delete_partner_entity(user, entity):
    return entity.user_can_delete(user)


@register.filter
def can_change_agreement(user, agreement):
    return agreement.user_can_change(user)


@register.filter
def can_delete_agreement(user, agreement):
    return agreement.user_can_delete(user)


@register.filter
def can_change_management_entity(user, management_entity):
    return management_entity.user_can_change(user)


@register.filter
def can_delete_management_entity(user, management_entity):
    return management_entity.user_can_delete(user)
