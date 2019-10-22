from django.conf.urls import url, include

from .views.configuration import ConfigurationView
from .views.partners import PartnersListView
from .views.partnerships import PartnershipsListView, PartnershipsRetrieveView

app_name = "partnership_api_v1"
urlpatterns = [
    url(r'^configuration$', ConfigurationView.as_view(), name='configuration'),
    url(r'^partners$', PartnersListView.as_view(), name='partners'),
    url(r'^partnerships', include(([
        url(r'^$', PartnershipsListView.as_view(), name='list'),
        url(r'^(?P<uuid>[0-9a-f-]+)$', PartnershipsRetrieveView.as_view(), name='retrieve'),
    ], "partnership_api_v1"), namespace='partnerships')),
]
