# subscriptions/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.http import FileResponse
import requests
from io import BytesIO
import logging
from .models import UserSubscription  
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.http import FileResponse
import requests
from io import BytesIO
import logging
from .models import UserSubscription  

logger = logging.getLogger(__name__)


logger = logging.getLogger(__name__)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import SavedCard
from .serializers import CardTokenizationSerializer, SavedCardSerializer
import logging
import razorpay
from django.conf import settings
from django.db import transaction

logger = logging.getLogger(__name__)
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import json
import razorpay
from django.conf import settings
from .models import UserSubscription

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
from .models import SubscriptionPlan, UserSubscription, SavedCard
from .serializers import (
    SubscriptionPlanSerializer,
    UserSubscriptionSerializer,
    CardTokenizationSerializer,
    InvoiceSerializer
)
from .utils import (
    create_razorpay_order,
    verify_razorpay_payment,
    check_card_type,
    generate_razorpay_invoice,
    create_razorpay_subscription,
    manage_razorpay_subscription
)
import razorpay
from decimal import Decimal
import traceback
import logging

logger = logging.getLogger(__name__)

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

class SubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get user's subscription details, available plans, and payment history."""
        try:
            user = request.user
            current_subscription = UserSubscription.objects.filter(
                user=user,
                is_active=True,
                end_date__gte=timezone.now()
            ).order_by('-start_date').first()

            available_plans = SubscriptionPlan.objects.filter(is_active=True)
            payment_history = UserSubscription.objects.filter(user=user).order_by('-created_at')

            current_subscription_data = UserSubscriptionSerializer(current_subscription).data if current_subscription else None
            available_plans_data = SubscriptionPlanSerializer(available_plans, many=True).data
            payment_history_data = UserSubscriptionSerializer(payment_history, many=True).data

            return Response({
                'current_subscription': current_subscription_data,
                'available_plans': available_plans_data,
                'payment_history': payment_history_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error fetching subscription details: {str(e)}")
            return Response({
                'error': f'Error fetching subscription details: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        """Create or update a subscription."""
        try:
            user = request.user
            plan_id = request.data.get('plan_id')
            razorpay_payment_id = request.data.get('razorpay_payment_id')
            razorpay_order_id = request.data.get('razorpay_order_id')
            razorpay_signature = request.data.get('razorpay_signature')

            if not plan_id:
                return Response({'error': 'Plan ID is required'}, status=status.HTTP_400_BAD_REQUEST)

            plan = SubscriptionPlan.objects.filter(id=plan_id, is_active=True).first()
            if not plan:
                return Response({'error': 'Invalid plan ID or plan is not active'}, status=status.HTTP_400_BAD_REQUEST)

            if not razorpay_payment_id:
                amount = plan.plan_choice.price
                if plan.discount_percentage:
                    discount = amount * (Decimal(str(plan.discount_percentage)) / Decimal('100'))
                    amount -= discount

                total_amount = amount
                if plan.plan_choice.gst_applicable:
                    total_amount += amount * Decimal('0.18')

                total_amount = total_amount.quantize(Decimal('0.01'))

                order = create_razorpay_order(total_amount)
                return Response({
                    'order_id': order['id'],
                    'amount': total_amount,
                    'currency': 'INR',
                    'razorpay_key': settings.RAZORPAY_KEY_ID
                }, status=status.HTTP_200_OK)

            if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature]):
                return Response({'error': 'Payment details are incomplete'}, status=status.HTTP_400_BAD_REQUEST)

            if not verify_razorpay_payment(razorpay_order_id, razorpay_payment_id, razorpay_signature):
                return Response({'error': 'Payment verification failed'}, status=status.HTTP_400_BAD_REQUEST)

            is_domestic_card = check_card_type(razorpay_payment_id)
            amount = plan.plan_choice.price
            if plan.discount_percentage:
                amount -= amount * (Decimal(str(plan.discount_percentage)) / Decimal('100'))

            total_amount = amount
            cgst = Decimal('0')
            sgst = Decimal('0')
            if plan.plan_choice.gst_applicable and is_domestic_card:
                gst_amount = amount * Decimal('0.18')
                cgst = gst_amount / 2
                sgst = gst_amount / 2
                total_amount += gst_amount

            UserSubscription.objects.filter(user=user, is_active=True).update(is_active=False)

            user_subscription = UserSubscription(
                user=user,
                subscription_plan=plan,
                amount=amount,
                payment_status='Success',
                transaction_id=razorpay_payment_id,
                is_domestic_card=is_domestic_card,
                start_date=timezone.now(),
                end_date=timezone.now() + timezone.timedelta(days=plan.plan_choice.duration_days),
                cgst=cgst,
                sgst=sgst,
                total_with_gst=total_amount
            )
            user_subscription.save()

            try:
                invoice_number = generate_razorpay_invoice(user_subscription)
                user_subscription.invoice_number = invoice_number
                user_subscription.invoice_id = invoice['id']
                user_subscription.save()
            except Exception as e:
                logger.error(f"Razorpay Invoice Error: {str(e)}")

            user.subscription_plan = plan
            user.credits += plan.plan_choice.credits
            user.save()

            return Response({
                'message': 'Subscription updated successfully',
                'subscription': UserSubscriptionSerializer(user_subscription).data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error processing subscription: {str(e)}")
            return Response({'error': f'Unexpected error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RefundRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Request a refund for a subscription."""
        user = request.user
        subscription_id = request.data.get('subscription_id')

        if not subscription_id:
            return Response({'error': 'Subscription ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            subscription = UserSubscription.objects.get(id=subscription_id, user=user, payment_status='Success')
        except UserSubscription.DoesNotExist:
            return Response({'error': 'Invalid subscription ID'}, status=status.HTTP_400_BAD_REQUEST)

        if subscription.refund_status:
            return Response({'error': 'Refund already requested or processed'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            refund = razorpay_client.payment.refund(subscription.transaction_id, {
                'amount': int(subscription.total_with_gst * 100),
                'speed': 'normal'
            })
            subscription.refund_status = 'Processed'
            subscription.refund_amount = subscription.total_with_gst
            subscription.payment_status = 'Refunded'
            subscription.is_active = False
            subscription.save()

            free_plan = SubscriptionPlan.objects.filter(plan_choice__is_default=True).first()
            if free_plan:
                user.subscription_plan = free_plan
                user.save()

            return Response({'message': 'Refund processed successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Refund processing failed: {str(e)}")
            return Response({'error': f'Refund failed: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

class CancelSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Cancel a subscription."""
        user = request.user
        subscription_id = request.data.get('subscription_id')
        cancel_reason = request.data.get('reason', 'User requested cancellation')

        if not subscription_id:
            return Response({'error': 'Subscription ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            subscription = UserSubscription.objects.get(id=subscription_id, user=user, is_active=True)
        except UserSubscription.DoesNotExist:
            return Response({'error': 'Invalid subscription ID or subscription is not active'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payment = razorpay_client.payment.fetch(subscription.transaction_id)
            original_amount = Decimal(payment['amount']) / 100 
            amount_refunded = Decimal(payment.get('amount_refunded', 0)) / 100
            available_refund = original_amount - amount_refunded
        except Exception as e:
            logger.error(f"Error fetching payment details: {str(e)}")
            return Response({'error': f'Failed to fetch payment details: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        remaining_days = (subscription.end_date - timezone.now()).days
        total_days = (subscription.end_date - subscription.start_date).days

        if remaining_days <= 0:
            return Response({'error': 'Subscription has already expired'}, status=status.HTTP_400_BAD_REQUEST)

        refund_percentage = Decimal(remaining_days) / Decimal(total_days)
        calculated_refund = subscription.total_with_gst * refund_percentage

        refund_amount = min(Decimal(calculated_refund), Decimal(available_refund))

        if refund_amount <= 0:
            return Response({'error': 'No refund amount available'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            try:
                refund_data = {
                    'amount': int(refund_amount * 100),  
                    'notes': {
                        'reason': cancel_reason,
                        'subscription_id': str(subscription_id)
                    }
                }

                refund = razorpay_client.payment.refund(subscription.transaction_id, refund_data)

                subscription.is_active = False
                subscription.payment_status = 'Refunded'
                subscription.refund_status = 'Processed'
                subscription.refund_amount = refund_amount
                subscription.save()

                total_credits = subscription.subscription_plan.plan_choice.credits
                credits_to_revert = int(total_credits * (remaining_days / total_days))

                user.credits = max(0, user.credits - credits_to_revert)

                free_plan = SubscriptionPlan.objects.filter(plan_choice__is_default=True).first()
                if free_plan:
                    user.subscription_plan = free_plan
                user.save()

                return Response({
                    'message': 'Subscription cancelled successfully',
                    'refund_amount': float(refund_amount),
                    'remaining_credits': user.credits,
                    'refund_details': {
                        'original_amount': float(original_amount),
                        'amount_already_refunded': float(amount_refunded),
                        'calculated_refund': float(calculated_refund),
                        'actual_refund': float(refund_amount)
                    }
                }, status=status.HTTP_200_OK)

            except Exception as e:
                logger.error(f"Transaction Error: {str(e)}")
                raise

class AutoRenewalSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Enable or disable auto-renewal for the current subscription."""
        user = request.user
        enable = request.data.get('enable', False)

        subscription = UserSubscription.objects.filter(user=user, is_active=True).first()

        if not subscription:
            return Response({'error': 'No active subscription found'}, status=status.HTTP_400_BAD_REQUEST)

        if subscription.razorpay_subscription_id:
            if enable:
                manage_razorpay_subscription(subscription.razorpay_subscription_id, 'resume')
            else:
                manage_razorpay_subscription(subscription.razorpay_subscription_id, 'cancel')

        subscription.auto_renewal = enable
        subscription.save()

        return Response({
            'message': f'Auto-renewal {"enabled" if enable else "disabled"} successfully'
        }, status=status.HTTP_200_OK)



class InvoiceManagementView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, invoice_id=None):
        """Get all invoices or download a specific invoice."""
        try:
            if invoice_id:
                try:
                    invoice = razorpay_client.invoice.fetch(invoice_id)
                except Exception as e:
                    logger.error(f"Error fetching invoice from Razorpay: {str(e)}")
                    return Response({'error': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)

                response = requests.get(invoice['short_url'])
                if response.status_code == 200:
                    buffer = BytesIO(response.content)
                    return FileResponse(
                        buffer,
                        as_attachment=True,
                        filename=f"invoice_{invoice['invoice_number']}.pdf"
                    )
                else:
                    return Response({'error': 'Failed to download invoice'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                subscriptions = UserSubscription.objects.filter(user=request.user).values_list('invoice_number', flat=True)

                invoices = []
                for invoice_number in subscriptions:
                    if invoice_number:
                        try:
                            invoice = razorpay_client.invoice.fetch(invoice_number)
                            invoices.append({
                                'invoice_id': invoice['id'],
                                'invoice_number': invoice['invoice_number'],
                                'subscription_id': invoice.get('subscription_id'),
                                'amount': float(invoice['amount']) / 100,  
                                'status': invoice['status'],
                                'date': invoice['created_at'],
                                'download_url': invoice['short_url']
                            })
                        except Exception as e:
                            logger.error(f"Error fetching invoice {invoice_number}: {str(e)}")
                            continue

                return Response({'invoices': invoices}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error fetching invoices: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CardManagementView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retrieve saved cards for the user."""
        try:
            cards = SavedCard.objects.filter(user=request.user, is_active=True)
            serializer = SavedCardSerializer(cards, many=True)
            return Response({
                'status': 'success',
                'cards': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving cards: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to retrieve cards',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create_razorpay_customer(self, user):
        """Create a new customer in Razorpay."""
        try:
            customer_data = {
                "name": f"{user.first_name} {user.last_name}".strip() or user.email,
                "email": user.email,
                "contact": user.phone_number or '9999999999',
                "fail_existing": 0
            }
            customer = razorpay_client.customer.create(data=customer_data)
            
            user.razorpay_customer_id = customer['id']
            user.save(update_fields=['razorpay_customer_id'])
            
            return customer['id']
        except Exception as e:
            logger.error(f"Error creating Razorpay customer: {str(e)}")
            raise

    def get_razorpay_customer_id(self, user):
        """Get or create Razorpay customer ID."""
        try:
            customer_id = user.razorpay_customer_id
            if not customer_id:
                customer_id = self.create_razorpay_customer(user)
            return customer_id
        except Exception as e:
            logger.error(f"Error getting/creating Razorpay customer: {str(e)}")
            raise

    @transaction.atomic
    def post(self, request):
        """Add a new card for the user."""
        try:
            serializer = CardTokenizationSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'status': 'error',
                    'message': 'Invalid card details',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                customer_id = self.get_razorpay_customer_id(request.user)
            except Exception as e:
                return Response({
                    'status': 'error',
                    'message': 'Failed to process customer details',
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            try:
                token_data = {
                    'customer_id': customer_id,
                    'method': 'card',
                    'card': {
                        'number': serializer.validated_data['card_number'],
                        'expiry_month': serializer.validated_data['expiry_month'],
                        'expiry_year': serializer.validated_data['expiry_year'],
                        'cvv': serializer.validated_data['cvv'],
                        'name': serializer.validated_data['name'],
                    }
                }
                
                razorpay_response = razorpay_client.token.create(data=token_data)
                
                if not razorpay_response or 'id' not in razorpay_response:
                    raise ValueError("Invalid response from Razorpay")

            except Exception as e:
                logger.error(f"Razorpay token creation failed: {str(e)}")
                return Response({
                    'status': 'error',
                    'message': 'Failed to tokenize card',
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                existing_card = SavedCard.objects.filter(
                    user=request.user,
                    card_last4=serializer.validated_data['card_number'][-4:],
                    expiry_month=serializer.validated_data['expiry_month'],
                    expiry_year=serializer.validated_data['expiry_year'],
                    is_active=True
                ).first()

                if existing_card:
                    return Response({
                        'status': 'error',
                        'message': 'Card already exists'
                    }, status=status.HTTP_400_BAD_REQUEST)

                card = SavedCard.objects.create(
                    user=request.user,
                    token_id=razorpay_response['id'],
                    card_last4=serializer.validated_data['card_number'][-4:],
                    card_network=razorpay_response.get('card', {}).get('network', '').lower(),
                    card_type=razorpay_response.get('card', {}).get('type', 'credit').lower(),
                    card_issuer=razorpay_response.get('card', {}).get('issuer', ''),
                    expiry_month=serializer.validated_data['expiry_month'],
                    expiry_year=serializer.validated_data['expiry_year'],
                    cardholder_name=serializer.validated_data['name'],
                    is_default=serializer.validated_data.get('is_default', False)
                )

                response_serializer = SavedCardSerializer(card)
                return Response({
                    'status': 'success',
                    'message': 'Card added successfully',
                    'card': response_serializer.data
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                logger.error(f"Error saving card details: {str(e)}")
                if razorpay_response and 'id' in razorpay_response:
                    try:
                        razorpay_client.token.delete(
                            customer_id=customer_id,
                            token_id=razorpay_response['id']
                        )
                    except Exception as delete_error:
                        logger.error(f"Error deleting Razorpay token after save failure: {str(delete_error)}")

                return Response({
                    'status': 'error',
                    'message': 'Failed to save card details',
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(f"Error processing card addition: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to process card addition',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request):
        """Update card details."""
        try:
            card_id = request.data.get('id')
            if not card_id:
                return Response({
                    'status': 'error',
                    'message': 'Card ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            card = SavedCard.objects.filter(
                id=card_id,
                user=request.user,
                is_active=True
            ).first()

            if not card:
                return Response({
                    'status': 'error',
                    'message': 'Card not found'
                }, status=status.HTTP_404_NOT_FOUND)

            update_data = {}
            if 'is_default' in request.data:
                update_data['is_default'] = request.data['is_default']
                if request.data['is_default']:
                    SavedCard.objects.filter(
                        user=request.user,
                        is_active=True,
                        is_default=True
                    ).exclude(id=card.id).update(is_default=False)

            if 'cardholder_name' in request.data:
                update_data['cardholder_name'] = request.data['cardholder_name']

            for key, value in update_data.items():
                setattr(card, key, value)
            card.save()

            serializer = SavedCardSerializer(card)
            return Response({
                'status': 'success',
                'message': 'Card updated successfully',
                'card': serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error updating card: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to update card',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        """Delete a saved card."""
        try:
            card_id = request.data.get('id')
            if not card_id:
                return Response({
                    'status': 'error',
                    'message': 'Card ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            card = SavedCard.objects.filter(
                id=card_id,
                user=request.user,
                is_active=True
            ).first()

            if not card:
                return Response({
                    'status': 'error',
                    'message': 'Card not found'
                }, status=status.HTTP_404_NOT_FOUND)

            customer_id = self.get_razorpay_customer_id(request.user)

            if card.token_id:
                try:
                    razorpay_client.token.delete(
                        customer_id=customer_id,
                        token_id=card.token_id
                    )
                except Exception as e:
                    logger.warning(f"Failed to delete Razorpay token: {str(e)}")

            card.is_active = False
            card.save()

            if card.is_default:
                other_card = SavedCard.objects.filter(
                    user=request.user,
                    is_active=True
                ).first()
                if other_card:
                    other_card.is_default = True
                    other_card.save()

            return Response({
                'status': 'success',
                'message': 'Card deleted successfully'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error deleting card: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to delete card',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class RazorpayWebhookHandler(APIView):
    def post(self, request):
        """Handle Razorpay webhook events."""
        try:
            payload = request.body
            signature = request.headers.get('X-Razorpay-Signature')

            razorpay_client.utility.verify_webhook_signature(payload, signature)

            event_data = json.loads(payload)
            if event_data['event'] == 'payment.captured':
                payment_id = event_data['payload']['payment']['entity']['id']

            elif event_data['event'] == 'subscription.activated':
                subscription_id = event_data['payload']['subscription']['entity']['id']
                

            return Response({'status': 'success'}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)