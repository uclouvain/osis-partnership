from django.conf.urls import include, url

from partnership.views import (EntityAutocompleteView,
                               PartnerAutocompletePartnershipsFilterView,
                               PartnerAutocompleteView, PartnerCreateView,
                               PartnerDetailView,
                               PartnerEntityAutocompletePartnershipsFilterView,
                               PartnerEntityAutocompleteView,
                               PartnerEntityCreateView,
                               PartnerEntityDeleteView,
                               PartnerEntityUpdateView, PartnerMediaCreateView,
                               PartnerMediaDeleteView, PartnerMediaUpdateView,
                               PartnersExportView, PartnershipAutocompleteView,
                               PartnershipContactCreateView,
                               PartnershipContactDeleteView,
                               PartnershipContactUpdateView,
                               PartnershipCreateView, PartnershipDetailView,
                               PartnershipExportView, PartnershipsListView,
                               PartnershipUpdateView, PartnersListView,
                               PartnerUpdateView,
                               PartneshipAgreementCreateView,
                               PartneshipAgreementDeleteView,
                               PartneshipAgreementUpdateView,
                               PartneshipConfigurationUpdateView,
                               PersonAutocompleteView, SimilarPartnerView,
                               UCLManagementEntityCreateView,
                               UCLManagementEntityDeleteView,
                               UCLManagementEntityDetailView,
                               UCLManagementEntityListView,
                               UCLManagementEntityUpdateView,
                               UclUniversityAutocompleteFilterView,
                               UclUniversityAutocompleteView,
                               UclUniversityLaboAutocompleteFilterView,
                               UclUniversityLaboAutocompleteView,
                               PartnershipYearEntitiesAutocompleteView,
                               PartnershipYearOffersAutocompleteView,
                               EntityAutocompleteView)


urlpatterns = [
    url(r'^$', PartnershipsListView.as_view(), name="list"),
    url(r'^export/$', PartnershipExportView.as_view(), name="export"),
    url(r'^configuration/$', PartneshipConfigurationUpdateView.as_view(), name='configuration_update'),
    url(r'^(?P<pk>\d+)/$', PartnershipDetailView.as_view(), name="detail"),
    url(r'^create/$', PartnershipCreateView.as_view(), name="create"),
    url(r'^(?P<pk>\d+)/update/$', PartnershipUpdateView.as_view(), name="update"),
    url(r'^(?P<partnership_pk>\d+)/contacts/', include([
        url(r'^new/$', PartnershipContactCreateView.as_view(), name="create"),
        url(r'^(?P<pk>\d+)/update/$', PartnershipContactUpdateView.as_view(), name="update"),
        url(r'^(?P<pk>\d+)/delete/$', PartnershipContactDeleteView.as_view(), name="delete"),
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
            url(r'^new/$', PartnerMediaCreateView.as_view(), name="create"),
            url(r'^(?P<pk>\d+)/update/$', PartnerMediaUpdateView.as_view(), name="update"),
            url(r'^(?P<pk>\d+)/delete/$', PartnerMediaDeleteView.as_view(), name="delete"),
        ], namespace='medias')),
        url(r'^(?P<partner_pk>\d+)/entities/', include([
            url(r'^new/$', PartnerEntityCreateView.as_view(), name="create"),
            url(r'^(?P<pk>\d+)/update/$', PartnerEntityUpdateView.as_view(), name="update"),
            url(r'^(?P<pk>\d+)/delete/$', PartnerEntityDeleteView.as_view(), name="delete"),
        ], namespace='entities')),
        url(r'^new/$', PartnerCreateView.as_view(), name="create"),
    ], namespace='partners')),
    url(r'^UCLManagementEntities/', include([
        url(r'^$', UCLManagementEntityListView.as_view(), name="list"),
        url(r'^create/$', UCLManagementEntityCreateView.as_view(), name="create"),
        url(r'^(?P<pk>\d+)/$', UCLManagementEntityDetailView.as_view(), name="detail"),
        url(r'^(?P<pk>\d+)/edit/$', UCLManagementEntityUpdateView.as_view(), name="update"),
        url(r'^(?P<pk>\d+)/delete/$', UCLManagementEntityDeleteView.as_view(), name="delete"),
    ], namespace='ucl_management_entities')),
    url(r'^autocomplete/', include([
        url('^person/$', PersonAutocompleteView.as_view(), name='person'),
        url('^partner/$', PartnerAutocompleteView.as_view(), name='partner'),
        url('^partnership/$', PartnershipAutocompleteView.as_view(), name='partnership'),
        url('^partner-entity/$', PartnerEntityAutocompleteView.as_view(), name='partner_entity'),
        url('^ucl_university/$', UclUniversityAutocompleteView.as_view(), name='ucl_university'),
        url('^ucl_university_labo/$', UclUniversityLaboAutocompleteView.as_view(), name='ucl_university_labo'),
        url('^partnership_year_entities/$', PartnershipYearEntitiesAutocompleteView.as_view(), name='partnership_year_entities'),
        url('^partnership_year_offers/$', PartnershipYearOffersAutocompleteView.as_view(), name='partnership_year_offers'),
        url('^entity/$', EntityAutocompleteView.as_view(), name='entity'),
        # Partnerships filter
        url(
            r'^partner-partnerships-filter/$',
            PartnerAutocompletePartnershipsFilterView.as_view(),
            name='partner_partnerships_filter',
        ),
        url(
            r'^partner-entity-partnerships-filter/$',
            PartnerEntityAutocompletePartnershipsFilterView.as_view(),
            name='partner_entity_partnerships_filter',
        ),
        url(
            r'^ucl_university_filter/$',
            UclUniversityAutocompleteFilterView.as_view(),
            name='ucl_university_filter',
        ),
        url(
            r'^ucl_university_labo_filter/$',
            UclUniversityLaboAutocompleteFilterView.as_view(),
            name='ucl_university_labo_filter',
        ),
    ], namespace='autocomplete')),
]
