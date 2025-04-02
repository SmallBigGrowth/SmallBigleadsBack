# Generated by Django 5.1.7 on 2025-04-02 07:28

import django.utils.timezone
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PlanChoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(choices=[('Free', 'Free'), ('Starter', 'Starter'), ('Professional', 'Professional'), ('Enterprise', 'Enterprise')], max_length=50, unique=True)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('credits', models.IntegerField()),
                ('duration_days', models.IntegerField()),
                ('description', models.TextField(blank=True, null=True)),
                ('gst_applicable', models.BooleanField(default=True)),
                ('is_default', models.BooleanField(default=False)),
                ('recurring_enabled', models.BooleanField(default=True)),
                ('razorpay_plan_id', models.CharField(blank=True, max_length=100, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('api_access', models.BooleanField(default=False)),
                ('bulk_processing_limit', models.IntegerField(blank=True, null=True)),
                ('max_users', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Plan Choice',
                'verbose_name_plural': 'Plan Choices',
                'ordering': ['price'],
            },
        ),
        migrations.CreateModel(
            name='SavedCard',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('token_id', models.CharField(max_length=100, unique=True)),
                ('card_last4', models.CharField(max_length=4)),
                ('card_network', models.CharField(max_length=20)),
                ('card_type', models.CharField(choices=[('credit', 'Credit Card'), ('debit', 'Debit Card')], max_length=20)),
                ('card_issuer', models.CharField(blank=True, max_length=50, null=True)),
                ('expiry_month', models.CharField(max_length=2)),
                ('expiry_year', models.CharField(max_length=4)),
                ('cardholder_name', models.CharField(max_length=255)),
                ('is_default', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-is_default', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='SubscriptionPlan',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('is_active', models.BooleanField(default=True)),
                ('discount_percentage', models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=5, null=True)),
                ('max_users', models.IntegerField(blank=True, null=True)),
                ('api_access', models.BooleanField(default=False)),
                ('bulk_processing_limit', models.IntegerField(blank=True, null=True)),
                ('referral_bonus_credits', models.IntegerField(default=0)),
                ('trial_period', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Subscription Plan',
                'verbose_name_plural': 'Subscription Plans',
                'ordering': ['plan_choice__price'],
            },
        ),
        migrations.CreateModel(
            name='UserSubscription',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('payment_status', models.CharField(choices=[('Pending', 'Pending'), ('Success', 'Success'), ('Failed', 'Failed'), ('Refunded', 'Refunded')], default='Pending', max_length=20)),
                ('transaction_id', models.CharField(blank=True, max_length=100, null=True)),
                ('razorpay_subscription_id', models.CharField(blank=True, max_length=100, null=True)),
                ('razorpay_order_id', models.CharField(blank=True, max_length=100, null=True)),
                ('razorpay_signature', models.CharField(blank=True, max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('start_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('end_date', models.DateTimeField()),
                ('next_billing_date', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('auto_renewal', models.BooleanField(default=True)),
                ('refund_status', models.CharField(blank=True, choices=[('Requested', 'Requested'), ('Processing', 'Processing'), ('Processed', 'Processed'), ('Failed', 'Failed'), ('Denied', 'Denied')], max_length=20, null=True)),
                ('refund_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('refund_id', models.CharField(blank=True, max_length=100, null=True)),
                ('invoice_number', models.CharField(blank=True, max_length=50, null=True, unique=True)),
                ('cgst', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('sgst', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('total_with_gst', models.DecimalField(decimal_places=2, max_digits=10)),
                ('is_domestic_card', models.BooleanField(default=True)),
                ('cancellation_reason', models.TextField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('invoice_id', models.CharField(blank=True, max_length=100, null=True)),
            ],
            options={
                'verbose_name': 'User Subscription',
                'verbose_name_plural': 'User Subscriptions',
                'ordering': ['-created_at'],
            },
        ),
    ]
