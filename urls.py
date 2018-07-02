from django.conf.urls import include, url
from partnership.views import (PartnerCreateView, PartnerDetailView,
                               PartnerEntityCreateView,
                               PartnerEntityDeleteView,
                               PartnerEntityUpdateView, PartnerMediaCreateView,
                               PartnerMediaDeleteView, PartnerMediaUpdateView,
                               PartnershipDetailView, PartnershipsListView,
                               PartnersListView, PartnerUpdateView,
                               PartnershipCreateView)

urlpatterns = [
    url(r'^$', PartnershipsListView.as_view(), name="partnerships_list"),
    url(r'^(?P<pk>\d+)/$', PartnershipDetailView.as_view(), name="partnership_detail"),
    url(r'^create/$', PartnershipCreateView.as_view(), name="partnership_create"),
    url(r'^partners/', include([
        url(r'^$', PartnersListView.as_view(), name="list"),
        url(r'^(?P<pk>\d+)/$', PartnerDetailView.as_view(), name="detail"),
        url(r'^(?P<pk>\d+)/update/$', PartnerUpdateView.as_view(), name="update"),
        url(r'^(?P<partner_pk>\d+)/medias/', include([
            url('^new/$', PartnerMediaCreateView.as_view(), name="create"),
            url(r'^(?P<pk>\d+)/update/$', PartnerMediaUpdateView.as_view(), name="update"),
            url(r'^(?P<pk>\d+)/delete/$', PartnerMediaDeleteView.as_view(), name="delete"),
        ], namespace='medias')),
        url(r'^(?P<partner_pk>\d+)/entities/', include([
            url('^new/$', PartnerEntityCreateView.as_view(), name="create"),
            url(r'^(?P<pk>\d+)/update/$', PartnerEntityUpdateView.as_view(), name="update"),
            url(r'^(?P<pk>\d+)/delete/$', PartnerEntityDeleteView.as_view(), name="delete"),
        ], namespace='entities')),
        url(r'^new/$', PartnerCreateView.as_view(), name="create"),
    ], namespace='partners')),
]
