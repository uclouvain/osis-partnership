from django.conf.urls import include
from django.urls import path, re_path

from .views.configuration import ConfigurationView
from .views.partners import PartnersListView
from .views.partnerships import PartnershipsListView, PartnershipsRetrieveView

app_name = "partnership_api_v1"
urlpatterns = [
    path('configuration', ConfigurationView.as_view(), name='configuration'),
    path('partners', PartnersListView.as_view(), name='partners'),
    path('partnerships/', include(([
        path('', PartnershipsListView.as_view(), name='list'),
        re_path(r'^(?P<uuid>[0-9a-f-]+)$', PartnershipsRetrieveView.as_view(), name='retrieve'),
    ], "partnership_api_v1"), namespace='partnerships')),
]
