from rest_framework import serializers
from .models import PlanChoice, SubscriptionPlan, UserSubscription, SavedCard
from django.utils import timezone
import re

class PlanChoiceSerializer(serializers.ModelSerializer):
    final_price = serializers.SerializerMethodField()
    
    class Meta:
        model = PlanChoice
        fields = [
            'id', 'name', 'price', 'credits', 'duration_days', 'description',
            'gst_applicable', 'is_default', 'recurring_enabled', 'razorpay_plan_id',
            'final_price', 'created_at', 'updated_at'
        ]
        read_only_fields = ['razorpay_plan_id', 'created_at', 'updated_at']

    def get_final_price(self, obj):
        if hasattr(obj, 'subscription_plans'):
            plan = obj.subscription_plans.first()
            if plan and plan.discount_percentage:
                return float(obj.price * (1 - plan.discount_percentage / 100))
        return float(obj.price)

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    plan_choice = PlanChoiceSerializer()
    final_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'plan_choice', 'is_active', 'discount_percentage', 'max_users',
            'api_access', 'bulk_processing_limit', 'referral_bonus_credits',
            'trial_period', 'final_price', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class SavedCardSerializer(serializers.ModelSerializer):
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = SavedCard
        fields = [
            'id', 'card_last4', 'card_network', 'card_type', 'card_issuer',
            'expiry_month', 'expiry_year', 'cardholder_name', 'is_default',
            'is_active', 'is_expired', 'created_at', 'updated_at'
        ]
        read_only_fields = ['token_id', 'created_at', 'updated_at']

    def get_is_expired(self, obj):
        current_year = timezone.now().year
        current_month = timezone.now().month
        card_year = int(obj.expiry_year)
        card_month = int(obj.expiry_month)
        
        return (card_year < current_year or 
                (card_year == current_year and card_month < current_month))

class UserSubscriptionSerializer(serializers.ModelSerializer):
    subscription_plan = SubscriptionPlanSerializer()
    saved_card = SavedCardSerializer(read_only=True)
    days_remaining = serializers.IntegerField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = UserSubscription
        fields = [
            'id', 'subscription_plan', 'saved_card', 'amount', 'payment_status',
            'transaction_id', 'razorpay_subscription_id', 'razorpay_order_id',
            'created_at', 'start_date', 'end_date', 'next_billing_date',
            'is_active', 'auto_renewal', 'refund_status', 'refund_amount',
            'refund_id', 'invoice_number', 'cgst', 'sgst', 'total_with_gst',
            'is_domestic_card', 'cancellation_reason', 'days_remaining',
            'is_expired', 'updated_at'
        ]
        read_only_fields = [
            'transaction_id', 'razorpay_subscription_id', 'razorpay_order_id',
            'created_at', 'updated_at', 'invoice_number', 'cgst', 'sgst',
            'total_with_gst', 'days_remaining', 'is_expired'
        ]

class CardTokenizationSerializer(serializers.Serializer):
    card_number = serializers.CharField(max_length=16)
    expiry_month = serializers.CharField(max_length=2)
    expiry_year = serializers.CharField(max_length=4)
    cvv = serializers.CharField(max_length=4, write_only=True)
    name = serializers.CharField(max_length=255)
    is_default = serializers.BooleanField(default=False)

    def validate_card_number(self, value):
        if not re.match(r'^\d{16}$', value):
            raise serializers.ValidationError("Card number must be 16 digits")
        return value

    def validate_expiry_month(self, value):
        try:
            month = int(value)
            if not (1 <= month <= 12):
                raise serializers.ValidationError("Invalid month")
        except ValueError:
            raise serializers.ValidationError("Month must be a number between 1 and 12")
        return value.zfill(2)

    def validate_expiry_year(self, value):
        try:
            year = int(value)
            current_year = timezone.now().year
            if not (current_year <= year <= current_year + 20):
                raise serializers.ValidationError("Invalid year")
        except ValueError:
            raise serializers.ValidationError("Invalid year format")
        return value

    def validate_cvv(self, value):
        if not re.match(r'^\d{3,4}$', value):
            raise serializers.ValidationError("CVV must be 3 or 4 digits")
        return value

    def validate(self, data):
        # Check if card is expired
        current_year = timezone.now().year
        current_month = timezone.now().month
        card_year = int(data['expiry_year'])
        card_month = int(data['expiry_month'])
        
        if (card_year < current_year or 
            (card_year == current_year and card_month < current_month)):
            raise serializers.ValidationError("Card has expired")
        return data

class InvoiceSerializer(serializers.Serializer):
    invoice_id = serializers.CharField()
    invoice_number = serializers.CharField()
    subscription_id = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    status = serializers.CharField()
    date = serializers.DateTimeField()
    download_url = serializers.URLField()
    gst_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_status = serializers.CharField()

class SubscriptionCancellationSerializer(serializers.Serializer):
    subscription_id = serializers.UUIDField()
    reason = serializers.CharField(required=False, allow_blank=True)
    request_refund = serializers.BooleanField(default=False)

class AutoRenewalSerializer(serializers.Serializer):
    enable = serializers.BooleanField()
    subscription_id = serializers.UUIDField(required=False)

class RefundRequestSerializer(serializers.Serializer):
    subscription_id = serializers.UUIDField()
    reason = serializers.CharField(required=False, allow_blank=True)
    full_refund = serializers.BooleanField(default=True)
    amount = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False,
        help_text="Required only if full_refund is False"
    )

    def validate(self, data):
        if not data.get('full_refund') and not data.get('amount'):
            raise serializers.ValidationError(
                "Amount is required when requesting partial refund"
            )
        return data