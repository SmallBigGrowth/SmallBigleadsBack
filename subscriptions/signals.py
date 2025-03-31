from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver
from .models import PlanChoice, SubscriptionPlan, UserSubscription
from django.utils import timezone
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

DEFAULT_PLANS = [
    {
        'name': 'Free',
        'price': 0.00,
        'credits': 10,
        'duration_days': 30,
        'gst_applicable': False,
        'is_default': True,
        'description': 'Free plan with basic features',
        'recurring_enabled': False,
        'max_users': 1,
        'api_access': False,
        'bulk_processing_limit': 100,
    },
    {
        'name': 'Starter',
        'price': 500.00,
        'credits': 100,
        'duration_days': 30,
        'gst_applicable': True,
        'is_default': False,
        'description': 'Starter plan for small users',
        'recurring_enabled': True,
        'max_users': 3,
        'api_access': True,
        'bulk_processing_limit': 1000,
    },
    {
        'name': 'Professional',
        'price': 1500.00,
        'credits': 500,
        'duration_days': 30,
        'gst_applicable': True,
        'is_default': False,
        'description': 'Professional plan for advanced users',
        'recurring_enabled': True,
        'max_users': 10,
        'api_access': True,
        'bulk_processing_limit': 5000,
    },
    {
        'name': 'Enterprise',
        'price': 5000.00,
        'credits': 2000,
        'duration_days': 90,
        'gst_applicable': True,
        'is_default': False,
        'description': 'Enterprise plan for large teams',
        'recurring_enabled': True,
        'max_users': 50,
        'api_access': True,
        'bulk_processing_limit': 25000,
    },
]

@receiver(post_migrate)
def create_default_plan_choices(sender, **kwargs):
    if sender.name == 'subscriptions':
        try:
            with transaction.atomic():
                for plan_data in DEFAULT_PLANS:
                    plan_choice, created = PlanChoice.objects.get_or_create(
                        name=plan_data['name'],
                        defaults=plan_data
                    )

                    if not created:
                        for key, value in plan_data.items():
                            setattr(plan_choice, key, value)
                        plan_choice.save()

                    subscription_plan_data = {
                        'is_active': True,
                        'max_users': plan_data.get('max_users', 1),
                        'api_access': plan_data.get('api_access', False),
                        'bulk_processing_limit': plan_data.get('bulk_processing_limit', 0),
                    }

                    SubscriptionPlan.objects.update_or_create(
                        plan_choice=plan_choice,
                        defaults=subscription_plan_data
                    )

                PlanChoice.objects.filter(is_default=True).exclude(name='Free').update(is_default=False)
                for plan in PlanChoice.objects.filter(
                    razorpay_plan_id__isnull=True,
                    recurring_enabled=True,
                    price__gt=0
                ):
                    plan.create_razorpay_plan()

            logger.info("Default plans and subscription plans created successfully")

        except Exception as e:
            logger.error(f"Error creating default plans: {str(e)}")
            raise

@receiver(post_save, sender=UserSubscription)
def handle_subscription_changes(sender, instance, created, **kwargs):
    try:
        if created:
            if instance.is_active:
                UserSubscription.objects.filter(
                    user=instance.user,
                    is_active=True
                ).exclude(id=instance.id).update(is_active=False)
                user = instance.user
                user.credits = instance.subscription_plan.plan_choice.credits
                user.save()

        elif instance.payment_status == 'Failed':
            instance.is_active = False
            instance.auto_renewal = False
            instance.save()

            free_plan = SubscriptionPlan.objects.filter(
                plan_choice__is_default=True,
                is_active=True
            ).first()

            if free_plan:
                instance.user.subscription_plan = free_plan
                instance.user.save()

    except Exception as e:
        logger.error(f"Error handling subscription changes: {str(e)}")