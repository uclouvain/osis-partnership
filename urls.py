from django.conf.urls import url, include

from partnership.views import PartnerCreateView, PartnerDetailView, PartnersListView, PartnershipsList, \
    PartnerUpdateView, PartnerMediaCreateView, PartnerMediaUpdateView, PartnerEntityCreateView, PartnerEntityUpdateView, \
    PartnerMediaDeleteView, PartnerEntityDeleteView

urlpatterns = [
    url(r'^$', PartnershipsList.as_view(), name="partnerships_list"),
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
