from django.db import models
from django.utils import timezone
import uuid
from django.conf import settings
import razorpay
from decimal import Decimal

class PlanChoice(models.Model):
    PLAN_CHOICES = [
        ('Free', 'Free'),
        ('Starter', 'Starter'),
        ('Professional', 'Professional'),
        ('Enterprise', 'Enterprise'),
    ]

    name = models.CharField(max_length=50, choices=PLAN_CHOICES, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    credits = models.IntegerField()
    duration_days = models.IntegerField()
    description = models.TextField(blank=True, null=True)
    gst_applicable = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    recurring_enabled = models.BooleanField(default=True)
    razorpay_plan_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    api_access = models.BooleanField(default=False)
    bulk_processing_limit = models.IntegerField(blank=True, null=True)
    max_users = models.IntegerField(blank=True, null=True)

    class Meta:
        ordering = ['price']
        verbose_name = "Plan Choice"
        verbose_name_plural = "Plan Choices"

    def __str__(self):
        return f"{self.name} (₹{self.price})"

    def save(self, *args, **kwargs):
        if not self.razorpay_plan_id and self.recurring_enabled and self.price > 0:
            self.create_razorpay_plan()
        super().save(*args, **kwargs)

    def create_razorpay_plan(self):
        try:
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

            if self.price > 0:
                plan_data = {
                    "period": "monthly",
                    "interval": 1,
                    "item": {
                        "name": self.name,
                        "amount": int(self.price * 100),
                        "currency": "INR",
                        "description": self.description or f"{self.name} Subscription Plan"
                    },
                    "notes": {
                        "plan_choice_id": str(self.id) if self.id else None,
                        "plan_name": self.name
                    }
                }

                razorpay_plan = client.plan.create(data=plan_data)
                self.razorpay_plan_id = razorpay_plan['id']
                return True
        except Exception as e:
            print(f"Error creating Razorpay plan: {str(e)}")
            return False

class SubscriptionPlan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan_choice = models.ForeignKey(PlanChoice, on_delete=models.CASCADE, related_name='subscription_plans')
    is_active = models.BooleanField(default=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True, null=True)
    max_users = models.IntegerField(blank=True, null=True)
    api_access = models.BooleanField(default=False)
    bulk_processing_limit = models.IntegerField(blank=True, null=True)
    referral_bonus_credits = models.IntegerField(default=0)
    trial_period = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['plan_choice__price']
        verbose_name = "Subscription Plan"
        verbose_name_plural = "Subscription Plans"

    def __str__(self):
        return f"{self.plan_choice.name} Plan"

    @property
    def final_price(self):
        """Calculate final price after discount"""
        if self.discount_percentage:
            discount = self.plan_choice.price * (Decimal(str(self.discount_percentage)) / Decimal('100'))
            return self.plan_choice.price - discount
        return self.plan_choice.price

class SavedCard(models.Model):
    CARD_TYPES = [
        ('credit', 'Credit Card'),
        ('debit', 'Debit Card'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='saved_cards')
    token_id = models.CharField(max_length=100, unique=True)
    card_last4 = models.CharField(max_length=4)
    card_network = models.CharField(max_length=20)  
    card_type = models.CharField(max_length=20, choices=CARD_TYPES)
    card_issuer = models.CharField(max_length=50, blank=True, null=True)  
    expiry_month = models.CharField(max_length=2)
    expiry_year = models.CharField(max_length=4)
    cardholder_name = models.CharField(max_length=255)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'card_last4', 'expiry_month', 'expiry_year')
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.card_network} **** {self.card_last4} ({self.cardholder_name})"

    def save(self, *args, **kwargs):
        if self.is_default:
            SavedCard.objects.filter(user=self.user).exclude(id=self.id).update(is_default=False)
        elif not SavedCard.objects.filter(user=self.user, is_default=True).exists():
            self.is_default = True
        super().save(*args, **kwargs)

class UserSubscription(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Success', 'Success'),
        ('Failed', 'Failed'),
        ('Refunded', 'Refunded')
    ]

    REFUND_STATUS_CHOICES = [
        ('Requested', 'Requested'),
        ('Processing', 'Processing'),
        ('Processed', 'Processed'),
        ('Failed', 'Failed'),
        ('Denied', 'Denied')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='subscriptions')
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    saved_card = models.ForeignKey(SavedCard, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_subscription_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    next_billing_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    auto_renewal = models.BooleanField(default=True)
    refund_status = models.CharField(max_length=20, choices=REFUND_STATUS_CHOICES, blank=True, null=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    refund_id = models.CharField(max_length=100, blank=True, null=True)
    invoice_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    cgst = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    sgst = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_with_gst = models.DecimalField(max_digits=10, decimal_places=2)
    is_domestic_card = models.BooleanField(default=True)
    cancellation_reason = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    invoice_id = models.CharField(max_length=100, blank=True, null=True)


    class Meta:
        ordering = ['-created_at']
        verbose_name = "User Subscription"
        verbose_name_plural = "User Subscriptions"

    def __str__(self):
        return f"{self.user.email} - {self.subscription_plan.plan_choice.name} - {self.invoice_number}"

    def save(self, *args, **kwargs):
        if not self.end_date:
            self.end_date = self.start_date + timezone.timedelta(days=self.subscription_plan.plan_choice.duration_days)

        if not self.next_billing_date and self.auto_renewal:
            self.next_billing_date = self.end_date

        if self.subscription_plan.plan_choice.gst_applicable and self.is_domestic_card:
            gst_rate = Decimal('0.18')
            self.cgst = self.amount * (gst_rate / 2)
            self.sgst = self.amount * (gst_rate / 2)
            self.total_with_gst = self.amount + self.cgst + self.sgst
        else:
            self.cgst = Decimal('0')
            self.sgst = Decimal('0')
            self.total_with_gst = self.amount

        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.end_date

    @property
    def days_remaining(self):
        if self.is_expired:
            return 0
        return (self.end_date - timezone.now()).days