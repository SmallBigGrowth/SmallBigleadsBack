# subscriptions/urls.py

from django.urls import path
from .views import (
    SubscriptionView,
    RefundRequestView,
    CancelSubscriptionView,
    AutoRenewalSubscriptionView,
    CardManagementView,
    InvoiceManagementView,
    RazorpayWebhookHandler
)

urlpatterns = [
    path('subscription/', SubscriptionView.as_view(), name='subscription'),
    path('subscription/refund/', RefundRequestView.as_view(), name='refund-request'),
    path('subscription/cancel/', CancelSubscriptionView.as_view(), name='cancel-subscription'),
    path('subscription/auto-renewal/', AutoRenewalSubscriptionView.as_view(), name='auto-renewal'),
    path('subscription/cards/', CardManagementView.as_view(), name='card-management'),
    path('subscription/invoices/', InvoiceManagementView.as_view(), name='invoice-management'),
    path('razorpay-webhook/', RazorpayWebhookHandler.as_view(), name='razorpay-webhook'),
    path('invoices/<str:invoice_id>/', InvoiceManagementView.as_view(), name='invoice-download'),
]