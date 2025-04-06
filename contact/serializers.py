from rest_framework import serializers
from .models import ContactEnrichment, BulkContactEnrichment

class ContactEnrichmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactEnrichment
        fields = '__all__'
        read_only_fields = ('status', 'created_at', 'updated_at')

class BulkContactEnrichmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = BulkContactEnrichment
        fields = '__all__'
        read_only_fields = ('status', 'total_records', 'processed_records', 'created_at', 'updated_at')

from rest_framework import serializers
from .models import ContactEnrichment, BulkContactEnrichment

class RecentLookupsSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()

    class Meta:
        model = ContactEnrichment
        fields = [
            'type', 'name', 'email', 'phone_number',
            'company_name', 'company_domain', 'linkedin_url', 'date'
        ]

    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_date(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M:%S")

class RecentFilesSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField()
    records = serializers.SerializerMethodField()

    class Meta:
        model = BulkContactEnrichment
        fields = ['file_name', 'status', 'records', 'date']

    def get_date(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M:%S")

    def get_records(self, obj):
        return f"{obj.processed_records}/{obj.total_records}"