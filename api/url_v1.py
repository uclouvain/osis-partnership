from django.conf.urls import url

from partnership.api.views import ConfigurationView, PartnersListView, PartnershipsListView

urlpatterns = [
    url(r'^configuration/$', ConfigurationView.as_view(), name='configuration'),
    url(r'^partners/$', PartnersListView.as_view(), name='partners'),
    url(r'^partnerships/$', PartnershipsListView.as_view(), name='parnterships'),
]
