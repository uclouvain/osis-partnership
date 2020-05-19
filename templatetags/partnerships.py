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
