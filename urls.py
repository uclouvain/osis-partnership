from django.conf.urls import url, include

from partnerships.views import PartnerDetail, PartnersList, PartnershipsList

urlpatterns = [
    url(r'^$', PartnershipsList.as_view(), name="partnerships_list"),
    url(r'^partners/', include([
        url(r'^$', PartnersList.as_view(), name="list"),
        url(r'^(?P<pk>\d+)/$', PartnerDetail.as_view(), name="detail"),
    ], namespace='partners')),
]
