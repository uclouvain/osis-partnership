from django.conf.urls import url

from partnerships.views import PartnerDetail, PartnersList, PartnershipsList

urlpatterns = [
    url(r'^$', PartnershipsList.as_view(), name="partnerships_list"),
    url(r'^partners/$', PartnersList.as_view(), name="partners_list"),
    url(r'^partners/(?P<pk>\d+)/$', PartnerDetail.as_view(), name="partner_detail"),
]
