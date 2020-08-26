from django.urls import include, path, re_path, register_converter

from .converters import PartnershipTypeConverter
from .views import *

register_converter(PartnershipTypeConverter, 'partnership_type')

app_name = "partnerships"
urlpatterns = [
    path('', PartnershipsListView.as_view(), name="list"),
    path('agreements/', PartnershipAgreementListView.as_view(), name="agreements-list"),
    path('export/<int:academic_year_pk>/', PartnershipExportView.as_view(), name="export"),
    path('export_agreements/', PartnershipAgreementExportView.as_view(), name="export_agreements"),
    path('configuration/', PartnershipConfigurationUpdateView.as_view(), name='configuration_update'),

    path('<int:pk>/', PartnershipDetailView.as_view(), name="detail"),
    path('create/', PartnershipTypeChooseView.as_view(), name="create"),
    path('create/<partnership_type:type>/', PartnershipCreateView.as_view(), name="create"),
    path('<int:pk>/update/', PartnershipUpdateView.as_view(), name="update"),
    path('<int:pk>/delete/', PartnershipDeleteView.as_view(), name="delete"),

    path('<int:partnership_pk>/contacts/', include(([
        path('new/', PartnershipContactCreateView.as_view(), name="create"),
        path('<int:pk>/update/', PartnershipContactUpdateView.as_view(), name="update"),
        path('<int:pk>/delete/', PartnershipContactDeleteView.as_view(), name="delete"),
    ], 'partnerships'), namespace='contacts')),

    path('<int:partnership_pk>/medias/', include(([
        path('new/', PartnershipMediaCreateView.as_view(), name="create"),
        path('<int:pk>/update/', PartnershipMediaUpdateView.as_view(), name="update"),
        path('<int:pk>/delete/', PartnershipMediaDeleteView.as_view(), name="delete"),
        path('<int:pk>/download/', PartnershipMediaDownloadView.as_view(), name="download"),
    ], 'partnerships'), namespace='medias')),

    path('<int:partnership_pk>/agreements/', include(([
        path('<int:pk>/delete/', PartnershipAgreementDeleteView.as_view(), name="delete"),
        path('<int:pk>/update/', PartnershipAgreementUpdateView.as_view(), name="update"),
        path('<int:pk>/download_media/', PartnershipAgreementMediaDownloadView.as_view(), name="download_media"),
        path('new/', PartnershipAgreementCreateView.as_view(), name="create"),
    ], 'partnerships'), namespace='agreements')),

    path('partners/', include(([
        path('', PartnersListView.as_view(), name="list"),
        path('export/', PartnersExportView.as_view(), name="export"),
        path('similar/', SimilarPartnerView.as_view(), name="similar"),
        path('<int:pk>/', PartnerDetailView.as_view(), name="detail"),
        path('<int:pk>/update/', PartnerUpdateView.as_view(), name="update"),
        path('<int:partner_pk>/medias/', include(([
            path('new/', PartnerMediaCreateView.as_view(), name="create"),
            path('<int:pk>/update/', PartnerMediaUpdateView.as_view(), name="update"),
            path('<int:pk>/delete/', PartnerMediaDeleteView.as_view(), name="delete"),
            path('<int:pk>/download/', PartnerMediaDownloadView.as_view(), name="download"),
        ], 'partnerships'), namespace='medias')),
        path('<int:partner_pk>/entities/', include(([
            path('new/', PartnerEntityCreateView.as_view(), name="create"),
            path('<int:pk>/update/', PartnerEntityUpdateView.as_view(), name="update"),
            path('<int:pk>/delete/', PartnerEntityDeleteView.as_view(), name="delete"),
        ], 'partnerships'), namespace='entities')),
        path('new/', PartnerCreateView.as_view(), name="create"),
    ], 'partnerships'), namespace='partners')),

    path('ucl_management_entities/', include(([
        path('', UCLManagementEntityListView.as_view(), name="list"),
        path('create/', UCLManagementEntityCreateView.as_view(), name="create"),
        path('<int:pk>/edit/', UCLManagementEntityUpdateView.as_view(), name="update"),
        path('<int:pk>/delete/', UCLManagementEntityDeleteView.as_view(), name="delete"),
    ], 'partnerships'), namespace='ucl_management_entities')),

    path('financings/', include(([
        re_path(r'^(?:(?P<year>\d{4})/)?$', FinancingListView.as_view(), name='list'),
        re_path(r'^(?:(?P<year>\d{4})/)?export/$', FinancingExportView.as_view(), name='export'),
        path('import/', FinancingImportView.as_view(), name='import'),
    ], 'partnerships'), namespace='financings')),

    path('autocomplete/', include(([
        path('person/', PersonAutocompleteView.as_view(), name='person'),
        path('partner/', PartnerAutocompleteView.as_view(), name='partner'),
        path('partnership/', PartnershipAutocompleteView.as_view(), name='partnership'),
        path('partner-entity/', PartnerEntityAutocompleteView.as_view(), name='partner_entity'),
        path('faculty_entity/', FacultyEntityAutocompleteView.as_view(), name='faculty_entity'),
        path('ucl_entity/', UclEntityAutocompleteView.as_view(), name='ucl_entity'),
        path('funding/', FundingAutocompleteView.as_view(), name='funding'),
        path('funding_program/', FundingProgramAutocompleteView.as_view(), name='funding_program'),
        path('funding_type/', FundingTypeAutocompleteView.as_view(), name='funding_type'),
        path('subtype/', PartnershipSubtypeAutocompleteView.as_view(), name='subtype'),
        path(
            'partnership_year_entities/',
            PartnershipYearEntitiesAutocompleteView.as_view(),
            name='partnership_year_entities',
        ),
        path(
            'partnership_year_offers/',
            PartnershipYearOffersAutocompleteView.as_view(),
            name='partnership_year_offers',
        ),

        # Partnerships filter
        path(
            'partner-partnerships-filter/',
            PartnerAutocompletePartnershipsFilterView.as_view(),
            name='partner_partnerships_filter',
        ),
        path(
            'partner-entity-partnerships-filter/',
            PartnerEntityAutocompletePartnershipsFilterView.as_view(),
            name='partner_entity_partnerships_filter',
        ),
        path(
            'ucl_entity_filter/',
            UclUniversityAutocompleteFilterView.as_view(),
            name='ucl_entity_filter',
        ),
        path(
            'years_entity_filter/',
            YearsEntityAutocompleteFilterView.as_view(),
            name='years_entity_filter',
        ),
        path(
            'offers_filter/',
            UniversityOffersAutocompleteFilterView.as_view(),
            name='university_offers_filter',
        ),
    ], 'partnerships'), namespace='autocomplete')),
]
