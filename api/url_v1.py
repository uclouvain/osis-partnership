from django.conf.urls import url, include

from .views.partnerships import PartnershipsListView, PartnershipsRetrieveView
from .views.partners import PartnersListView
from .views.configuration import ConfigurationView


app_name = "partnership"
urlpatterns = [
    url(r'^configuration$', ConfigurationView.as_view(), name='configuration'),
    url(r'^partners$', PartnersListView.as_view(), name='partners'),
    url(r'^partnerships', include([
        url(r'^$', PartnershipsListView.as_view(), name='list'),
        url(r'^/(?P<uuid>[0-9a-f-]+)$', PartnershipsRetrieveView.as_view(), name='retrieve'),
    ], namespace='partnerships')),
]
