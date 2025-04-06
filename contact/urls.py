from django.urls import path
from .views import ContactEnrichmentViewSet, BulkContactEnrichmentViewSet,EnrichmentView

urlpatterns = [
    path('contact-enrichment/enrich_contact/',
         ContactEnrichmentViewSet.as_view({'post': 'enrich_contact'}),
         name='contact-enrich'),

    path('contact-enrichment/recent_lookups/',
         ContactEnrichmentViewSet.as_view({'get': 'recent_lookups'}),
         name='recent-lookups'),

    path('bulk-enrichment/bulk_enrich/',
         BulkContactEnrichmentViewSet.as_view({'post': 'bulk_enrich'}),
         name='bulk-enrich'),

    path('bulk-enrichment/recent_files/',
         BulkContactEnrichmentViewSet.as_view({'get': 'recent_files'}),
         name='recent-files'),
    path("enrich/", EnrichmentView.as_view(), name="enrich"),
]