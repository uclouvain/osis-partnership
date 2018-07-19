from django.conf.urls import include, url

from partnership.views import (PartnerCreateView, PartnerDetailView,
                               PartnerEntityCreateView,
                               PartnerEntityDeleteView,
                               PartnerEntityUpdateView, PartnerMediaCreateView,
                               PartnerMediaDeleteView, PartnerMediaUpdateView,
                               PartnershipDetailView, PartnershipsListView,
                               PartnersListView, PartnerUpdateView, SimilarPartnerView,
                               PartnershipCreateView, UclUniversityAutocompleteView,
                               UniversityOffersAutocompleteView, PartnershipUpdateView,
                               UniversityOffersAutocompleteFilterView,
                               UclUniversityAutocompleteFilterView,
                               UclUniversityLaboAutocompleteFilterView, PartnersExportView,
                               PartnershipContactCreateView, PartnershipContactUpdateView,
                               PartnershipContactDeleteView,
                               PartneshipAgreementDeleteView, PartneshipAgreementUpdateView,
                               PartneshipAgreementCreateView, PersonAutocompleteView, PartneshipConfigurationUpdateView)

urlpatterns = [
    url(r'^$', PartnershipsListView.as_view(), name="partnerships_list"),
    url(r'^configuration/$', PartneshipConfigurationUpdateView.as_view(), name='configuration_update'),
    url(r'^(?P<pk>\d+)/$', PartnershipDetailView.as_view(), name="partnership_detail"),
    url(r'^create/$', PartnershipCreateView.as_view(), name="partnership_create"),
    url(r'^(?P<pk>\d+)/update/$', PartnershipUpdateView.as_view(), name="partnership_update"),
    url(r'^(?P<partnership_pk>\d+)/contacts/', include([
        url('^new/$', PartnershipContactCreateView.as_view(), name="create"),
        url('^(?P<pk>\d+)/update/$', PartnershipContactUpdateView.as_view(), name="update"),
        url('^(?P<pk>\d+)/delete/$', PartnershipContactDeleteView.as_view(), name="delete"),
    ], namespace='contacts')),
    url(r'^(?P<partnership_pk>\d+)/agreements/', include([
        url(r'^(?P<pk>\d+)/delete/$', PartneshipAgreementDeleteView.as_view(), name="delete"),
        url(r'^(?P<pk>\d+)/update/$', PartneshipAgreementUpdateView.as_view(), name="update"),
        url(r'^new/$', PartneshipAgreementCreateView.as_view(), name="create"),
    ], namespace='agreements')),
    url(r'^partners/', include([
        url(r'^$', PartnersListView.as_view(), name="list"),
        url(r'^export/$', PartnersExportView.as_view(), name="export"),
        url(r'^similar/$', SimilarPartnerView.as_view(), name="similar"),
        url(r'^(?P<pk>\d+)/$', PartnerDetailView.as_view(), name="detail"),
        url(r'^(?P<pk>\d+)/update/$', PartnerUpdateView.as_view(), name="update"),
        url(r'^(?P<partner_pk>\d+)/medias/', include([
            url('^new/$', PartnerMediaCreateView.as_view(), name="create"),
            url(r'^(?P<pk>\d+)/update/$', PartnerMediaUpdateView.as_view(), name="update"),
            url(r'^(?P<pk>\d+)/delete/$', PartnerMediaDeleteView.as_view(), name="delete"),
        ], namespace='medias')),
        url(r'^(?P<partner_pk>\d+)/entities/', include([
            url('^new/$', PartnerEntityCreateView.as_view(), name="create"),
            url(r'^(?P<pk>\d+)/update/$', PartnerEntityUpdateView.as_view(), name="update"),
            url(r'^(?P<pk>\d+)/delete/$', PartnerEntityDeleteView.as_view(), name="delete"),
        ], namespace='entities')),
        url(r'^new/$', PartnerCreateView.as_view(), name="create"),
    ], namespace='partners')),
    url(r'^autocomplete/', include([
        url(
            '^person/$',
            PersonAutocompleteView.as_view(),
            name='person'
        ),
        url(
            '^ucl_university/$',
            UclUniversityAutocompleteView.as_view(),
            name='ucl_university'
        ),
        url(
            '^ucl_university_filter/$',
            UclUniversityAutocompleteFilterView.as_view(),
            name='ucl_university_filter'
        ),
        url(
            '^ucl_university_labo_filter/$',
            UclUniversityLaboAutocompleteFilterView.as_view(),
            name='ucl_university_labo_filter'
        ),
        url(
            '^university_offers/$',
            UniversityOffersAutocompleteView.as_view(),
            name='university_offers'
        ),
        url(
            '^university_offers_filter/$',
            UniversityOffersAutocompleteFilterView.as_view(),
            name='university_offers_filter'
        ),
    ], namespace='autocomplete')),
]
