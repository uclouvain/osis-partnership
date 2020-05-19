from django.conf.urls import include, url

from .views import *

app_name = "partnerships"
urlpatterns = [
    url(r'^$', PartnershipsListView.as_view(), name="list"),
    url(r'^agreements/$', PartnershipAgreementListView.as_view(), name="agreements-list"),
    url(r'^export/$', PartnershipExportView.as_view(), name="export"),
    url(r'^export_agreements/$', PartnershipAgreementExportView.as_view(), name="export_agreements"),
    url(r'^configuration/$', PartnershipConfigurationUpdateView.as_view(), name='configuration_update'),
    url(r'^(?P<pk>\d+)/$', PartnershipDetailView.as_view(), name="detail"),
    url(r'^create/$', PartnershipCreateView.as_view(), name="create"),
    url(r'^(?P<pk>\d+)/update/$', PartnershipUpdateView.as_view(), name="update"),
    url(r'^(?P<partnership_pk>\d+)/contacts/', include(([
        url(r'^new/$', PartnershipContactCreateView.as_view(), name="create"),
        url(r'^(?P<pk>\d+)/update/$', PartnershipContactUpdateView.as_view(), name="update"),
        url(r'^(?P<pk>\d+)/delete/$', PartnershipContactDeleteView.as_view(), name="delete"),
    ], 'partnerships'), namespace='contacts')),
    url(r'^(?P<partnership_pk>\d+)/medias/', include(([
        url(r'^new/$', PartnershipMediaCreateView.as_view(), name="create"),
        url(r'^(?P<pk>\d+)/update/$', PartnershipMediaUpdateView.as_view(), name="update"),
        url(r'^(?P<pk>\d+)/delete/$', PartnershipMediaDeleteView.as_view(), name="delete"),
        url(r'^(?P<pk>\d+)/download/$', PartnershipMediaDownloadView.as_view(), name="download"),
    ], 'partnerships'), namespace='medias')),
    url(r'^(?P<partnership_pk>\d+)/agreements/', include(([
        url(r'^(?P<pk>\d+)/delete/$', PartnershipAgreementDeleteView.as_view(), name="delete"),
        url(r'^(?P<pk>\d+)/update/$', PartnershipAgreementUpdateView.as_view(), name="update"),
        url(r'^(?P<pk>\d+)/download_media/$', PartnershipAgreementMediaDownloadView.as_view(), name="download_media"),
        url(r'^new/$', PartnershipAgreementCreateView.as_view(), name="create"),
    ], 'partnerships'), namespace='agreements')),
    url(r'^partners/', include(([
        url(r'^$', PartnersListView.as_view(), name="list"),
        url(r'^export/$', PartnersExportView.as_view(), name="export"),
        url(r'^similar/$', SimilarPartnerView.as_view(), name="similar"),
        url(r'^(?P<pk>\d+)/$', PartnerDetailView.as_view(), name="detail"),
        url(r'^(?P<pk>\d+)/update/$', PartnerUpdateView.as_view(), name="update"),
        url(r'^(?P<partner_pk>\d+)/medias/', include(([
            url(r'^new/$', PartnerMediaCreateView.as_view(), name="create"),
            url(r'^(?P<pk>\d+)/update/$', PartnerMediaUpdateView.as_view(), name="update"),
            url(r'^(?P<pk>\d+)/delete/$', PartnerMediaDeleteView.as_view(), name="delete"),
            url(r'^(?P<pk>\d+)/download/$', PartnerMediaDownloadView.as_view(), name="download"),
        ], 'partnerships'), namespace='medias')),
        url(r'^(?P<partner_pk>\d+)/entities/', include(([
            url(r'^new/$', PartnerEntityCreateView.as_view(), name="create"),
            url(r'^(?P<pk>\d+)/update/$', PartnerEntityUpdateView.as_view(), name="update"),
            url(r'^(?P<pk>\d+)/delete/$', PartnerEntityDeleteView.as_view(), name="delete"),
        ], 'partnerships'), namespace='entities')),
        url(r'^new/$', PartnerCreateView.as_view(), name="create"),
    ], 'partnerships'), namespace='partners')),
    url(r'^ucl_management_entities/', include(([
        url(r'^$', UCLManagementEntityListView.as_view(), name="list"),
        url(r'^create/$', UCLManagementEntityCreateView.as_view(), name="create"),
        url(r'^(?P<pk>\d+)/edit/$', UCLManagementEntityUpdateView.as_view(), name="update"),
        url(r'^(?P<pk>\d+)/delete/$', UCLManagementEntityDeleteView.as_view(), name="delete"),
    ], 'partnerships'), namespace='ucl_management_entities')),
    url(r'^financings/', include(([
        url(r'^(?:(?P<year>\d{4})/)?$', FinancingListView.as_view(), name='list'),
        url(r'^(?:(?P<year>\d{4})/)?export/$', FinancingExportView.as_view(), name='export'),
        url(r'^import/$', FinancingImportView.as_view(), name='import'),
    ], 'partnerships'), namespace='financings')),
    url(r'^autocomplete/', include(([
        url('^person/$', PersonAutocompleteView.as_view(), name='person'),
        url('^partner/$', PartnerAutocompleteView.as_view(), name='partner'),
        url('^partnership/$', PartnershipAutocompleteView.as_view(), name='partnership'),
        url('^partner-entity/$', PartnerEntityAutocompleteView.as_view(), name='partner_entity'),
        url('^faculty_entity/$', FacultyEntityAutocompleteView.as_view(), name='faculty_entity'),
        url('^ucl_entity/$', UclEntityAutocompleteView.as_view(), name='ucl_entity'),
        url(
            '^partnership_year_entities/$',
            PartnershipYearEntitiesAutocompleteView.as_view(),
            name='partnership_year_entities',
        ),
        url(
            '^partnership_year_offers/$',
            PartnershipYearOffersAutocompleteView.as_view(),
            name='partnership_year_offers',
        ),
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
            r'^ucl_entity_filter/$',
            UclUniversityAutocompleteFilterView.as_view(),
            name='ucl_entity_filter',
        ),
        url(
            '^years_entity_filter/$',
            YearsEntityAutocompleteFilterView.as_view(),
            name='years_entity_filter'
        ),
        url('^offers_filter/$', UniversityOffersAutocompleteFilterView.as_view(), name='university_offers_filter'),
    ], 'partnerships'), namespace='autocomplete')),
]
