from django.conf.urls import include
from django.urls import path, re_path

from .views.configuration import ConfigurationView
from .views.partners import PartnersApiListView
from .views.partnerships import (
    PartnershipsApiExportView,
    PartnershipsApiListView,
    PartnershipsApiRetrieveView,
    partnership_get_export_url,
)

app_name = "partnership_api_v1"
urlpatterns = [
    path('configuration', ConfigurationView.as_view(), name='configuration'),
    path('partners', PartnersApiListView.as_view(), name='partners'),
    path('partnerships', PartnershipsApiListView.as_view(), name='partnerships'),
    path('partnerships/get-export-url', partnership_get_export_url, name='get-export-url'),
    path('partnerships/export', PartnershipsApiExportView.as_view(), name='export'),
    re_path(r'^partnerships/(?P<uuid>[0-9a-f-]+)$', PartnershipsApiRetrieveView.as_view(), name='retrieve'),
]
