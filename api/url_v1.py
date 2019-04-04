from django.conf.urls import url

from partnership.api.views import ConfigurationView, PartnersListView, PartnershipsListView

urlpatterns = [
    url(r'^configuration/$', ConfigurationView.as_view(), name=''),
    url(r'^partners/$', PartnersListView.as_view(), name=''),
    url(r'^$', PartnershipsListView.as_view(), name=''),
]
