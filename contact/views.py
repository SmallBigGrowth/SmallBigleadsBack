from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ContactEnrichment, BulkContactEnrichment
from .serializers import ContactEnrichmentSerializer, BulkContactEnrichmentSerializer
from .services import BetterContactAPI
class ContactEnrichmentViewSet(viewsets.ViewSet): 
    serializer_class = ContactEnrichmentSerializer

    @action(detail=False, methods=['post'])
    def enrich_contact(self, request):
        email = request.data.get('email')
        if not email:
            return Response(
                {'error': 'Email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            contact = ContactEnrichment.objects.create(email=email)
            better_contact = BetterContactAPI()
            enrichment_data = better_contact.enrich_single_contact(email)
            contact.first_name = enrichment_data.get('first_name')
            contact.last_name = enrichment_data.get('last_name')
            contact.company_name = enrichment_data.get('company_name')
            contact.job_title = enrichment_data.get('job_title')
            contact.linkedin_url = enrichment_data.get('linkedin_url')
            contact.phone_number = enrichment_data.get('phone_number')
            contact.status = 'completed'
            contact.save()

            serializer = ContactEnrichmentSerializer(contact)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            if 'contact' in locals():
                contact.status = 'failed'
                contact.save()
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def recent_lookups(self, request):
        recent_lookups = ContactEnrichment.objects.all().order_by('-created_at')[:10]
        serializer = ContactEnrichmentSerializer(recent_lookups, many=True)
        return Response(serializer.data)

class BulkContactEnrichmentViewSet(viewsets.ViewSet): 
    serializer_class = BulkContactEnrichmentSerializer

    @action(detail=False, methods=['post'])
    def bulk_enrich(self, request):
        if 'file' not in request.FILES:
            return Response(
                {'error': 'File is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        file = request.FILES['file']

        try:
            file_path = default_storage.save(f'contact_files/{file.name}', file)
            bulk_enrichment = BulkContactEnrichment.objects.create(
                file_name=file.name,
                file=file_path,
                status='processing'
            )

            df = pd.read_csv(file_path)
            bulk_enrichment.total_records = len(df)
            bulk_enrichment.save()

            better_contact = BetterContactAPI()
            enrichment_result = better_contact.enrich_bulk_contacts(file_path)

            bulk_enrichment.status = 'completed'
            bulk_enrichment.processed_records = bulk_enrichment.total_records
            bulk_enrichment.save()

            serializer = BulkContactEnrichmentSerializer(bulk_enrichment)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            if 'bulk_enrichment' in locals():
                bulk_enrichment.status = 'failed'
                bulk_enrichment.save()
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def recent_files(self, request):
        recent_files = BulkContactEnrichment.objects.all().order_by('-created_at')[:10]
        serializer = BulkContactEnrichmentSerializer(recent_files, many=True)
        return Response(serializer.data)

# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import DataEnrichmentService

class EmailLookupView(APIView):
    def post(self, request):
        contact_details = {
            "first_name": request.data.get("first_name"),
            "last_name": request.data.get("last_name"),
            "company_name": request.data.get("company_name"),
            "company_domain": request.data.get("company_domain"),
            "linkedin_profile": request.data.get("linkedin_profile")
        }

        required_fields = ["first_name", "last_name", "company_domain"]
        missing_fields = [field for field in required_fields if not contact_details.get(field)]

        if missing_fields:
            return Response(
                {
                    "error": f"Missing required fields: {', '.join(missing_fields)}",
                    "required_fields": required_fields
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        service = DataEnrichmentService()
        try:
            result = service.get_email_data(contact_details)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {
                    "error": str(e),
                    "detail": "An error occurred while looking up email"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

