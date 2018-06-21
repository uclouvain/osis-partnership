from django.conf.urls import url, include

from partnership.views import PartnerCreateView, PartnerDetailView, PartnersListView, PartnershipsList, \
    PartnerUpdateView, PartnerMediaCreateView

urlpatterns = [
    url(r'^$', PartnershipsList.as_view(), name="partnerships_list"),
    url(r'^partners/', include([
        url(r'^$', PartnersListView.as_view(), name="list"),
        url(r'^(?P<pk>\d+)/$', PartnerDetailView.as_view(), name="detail"),
        url(r'^(?P<pk>\d+)/update/$', PartnerUpdateView.as_view(), name="update"),
        url(r'^(?P<partner_pk>\d+)/media/', include([
            url('^new/$', PartnerMediaCreateView.as_view(), name="create"),
        ], namespace='medias')),
        url(r'^new/$', PartnerCreateView.as_view(), name="create"),
    ], namespace='partners')),
]
