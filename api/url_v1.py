from django.conf.urls import url, include

from partnership.api.views import ConfigurationView, PartnersListView, PartnershipsListView, PartnershipsRetrieveView

urlpatterns = [
    url(r'^configuration/$', ConfigurationView.as_view(), name='configuration'),
    url(r'^partners/$', PartnersListView.as_view(), name='partners'),
    url(r'^partnerships/', include([
        url(r'^$', PartnershipsListView.as_view(), name='list'),
        url(r'^(?P<uuid>[0-9a-f-]+)/$', PartnershipsRetrieveView.as_view(), name='retrieve'),
    ], namespace='partnerships')),
]
