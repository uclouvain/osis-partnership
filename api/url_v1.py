from django.conf.urls import url, include

from .views.medias import MediaDownloadView, MediaMetadataRetrieveView
from .views.partnerships import PartnershipsListView, PartnershipsRetrieveView
from .views.partners import PartnersListView
from .views.configuration import ConfigurationView

urlpatterns = [
    url(r'^configuration$', ConfigurationView.as_view(), name='configuration'),
    url(r'^partners$', PartnersListView.as_view(), name='partners'),
    url(r'^partnerships', include([
        url(r'^$', PartnershipsListView.as_view(), name='list'),
        url(r'^/(?P<uuid>[0-9a-f-]+)$', PartnershipsRetrieveView.as_view(), name='retrieve'),
    ], namespace='partnerships')),
    url(r'^medias/(?P<uuid>[0-9a-f-]+)', include([
        url(r'^$', MediaMetadataRetrieveView.as_view(), name='list'),
        url(r'^/download', MediaDownloadView.as_view(), name='download'),
    ], namespace='medias')),
]
