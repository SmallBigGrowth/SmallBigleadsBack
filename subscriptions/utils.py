import razorpay
from django.conf import settings
from rest_framework.exceptions import ValidationError
from datetime import datetime, timedelta
import logging
import json
import requests
from decimal import Decimal

logger = logging.getLogger(__name__)

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def get_razorpay_client():
    """Get a new Razorpay client instance"""
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def create_razorpay_customer(user):
    """Create a new customer in Razorpay"""
    try:
        customer_data = {
            "name": f"{user.first_name} {user.last_name}".strip(),
            "email": user.email,
            "contact": getattr(user, 'phone_number', ''),
            "notes": {
                "user_id": str(user.id),
                "email": user.email
            }
        }
        return razorpay_client.customer.create(data=customer_data)
    except Exception as e:
        logger.error(f"Error creating Razorpay customer: {str(e)}")
        raise ValidationError(f"Failed to create customer: {str(e)}")

def create_razorpay_subscription(plan_id, customer_id=None, total_count=12):
    """Create a new subscription in Razorpay"""
    try:
        subscription_data = {
            "plan_id": plan_id,
            "total_count": total_count,
            "quantity": 1,
            "customer_notify": 1,
            "notify_info": {
                "notify_phone": 1,
                "notify_email": 1
            }
        }

        if customer_id:
            subscription_data["customer_id"] = customer_id

        subscription = razorpay_client.subscription.create(data=subscription_data)
        logger.info(f"Created Razorpay subscription: {subscription['id']}")
        return subscription
    except Exception as e:
        logger.error(f"Error creating Razorpay subscription: {str(e)}")
        raise ValidationError(f"Failed to create subscription: {str(e)}")

def create_razorpay_order(amount, currency="INR", receipt=None, notes=None):
    """Create a new order in Razorpay"""
    try:
        order_data = {
            "amount": int(amount * 100),
            "currency": currency,
            "payment_capture": 1
        }

        if receipt:
            order_data["receipt"] = receipt
        if notes:
            order_data["notes"] = notes

        order = razorpay_client.order.create(data=order_data)
        logger.info(f"Created Razorpay order: {order['id']}")
        return order
    except Exception as e:
        logger.error(f"Error creating Razorpay order: {str(e)}")
        raise ValidationError(f"Failed to create order: {str(e)}")

def verify_razorpay_payment(order_id, payment_id, signature):
    """Verify Razorpay payment signature"""
    try:
        payment_data = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }

        razorpay_client.utility.verify_payment_signature(payment_data)
        logger.info(f"Payment verified: {payment_id}")
        return True
    except Exception as e:
        logger.error(f"Payment verification failed: {str(e)}")
        return False

def check_card_type(payment_id):
    """Check if the card is domestic or international"""
    try:
        payment = razorpay_client.payment.fetch(payment_id)

        if payment['method'] != 'card':
            raise ValidationError("Only card payments are allowed")

        card_info = payment.get('card', {})
        is_domestic = not card_info.get('international', False)

        logger.info(f"Card type checked for payment {payment_id}: {'Domestic' if is_domestic else 'International'}")
        return is_domestic
    except Exception as e:
        logger.error(f"Error checking card type: {str(e)}")
        raise ValidationError(f"Failed to check card type: {str(e)}")

def generate_razorpay_invoice(user_subscription):
    """Generate a new invoice in Razorpay"""
    try:
        customer_data = {
            "name": f"{user_subscription.user.first_name} {user_subscription.user.last_name}".strip(),
            "email": user_subscription.user.email
        }

        line_items = [{
            "name": user_subscription.subscription_plan.plan_choice.name,
            "description": user_subscription.subscription_plan.plan_choice.description or "Subscription Payment",
            "amount": int(user_subscription.amount * 100),
            "currency": "INR",
            "quantity": 1
        }]

        if user_subscription.cgst:
            line_items.append({
                "name": "CGST",
                "amount": int(user_subscription.cgst * 100),
                "currency": "INR",
                "quantity": 1
            })

        if user_subscription.sgst:
            line_items.append({
                "name": "SGST",
                "amount": int(user_subscription.sgst * 100),
                "currency": "INR",
                "quantity": 1
            })

        invoice_data = {
            "type": "invoice",
            "description": f"Subscription Invoice - {user_subscription.subscription_plan.plan_choice.name}",
            "customer": customer_data,
            "line_items": line_items,
            "currency": "INR",
            "sms_notify": 0,
            "email_notify": 1,
            "notes": {
                "subscription_id": str(user_subscription.id),
                "user_id": str(user_subscription.user.id)
            }
        }

        invoice = razorpay_client.invoice.create(data=invoice_data)
        logger.info(f"Generated invoice: {invoice['id']}")
        return invoice['id']

    except Exception as e:
        logger.error(f"Error generating invoice: {str(e)}")
        raise ValidationError(f"Failed to generate invoice: {str(e)}")

def manage_razorpay_subscription(subscription_id, action):
    """Manage Razorpay subscription (cancel, pause, resume)"""
    try:
        if action == 'cancel':
            result = razorpay_client.subscription.cancel(subscription_id)
            logger.info(f"Cancelled subscription: {subscription_id}")
        elif action == 'pause':
            result = razorpay_client.subscription.pause(subscription_id)
            logger.info(f"Paused subscription: {subscription_id}")
        elif action == 'resume':
            result = razorpay_client.subscription.resume(subscription_id)
            logger.info(f"Resumed subscription: {subscription_id}")
        else:
            raise ValidationError(f"Invalid action: {action}")

        return result
    except Exception as e:
        logger.error(f"Error managing subscription: {str(e)}")
        raise ValidationError(f"Failed to {action} subscription: {str(e)}")

def process_refund(payment_id, amount=None, notes=None):
    """Process refund for a payment"""
    try:
        refund_data = {
            "notes": notes or {}
        }

        if amount:
            refund_data["amount"] = int(amount * 100)

        refund = razorpay_client.payment.refund(payment_id, refund_data)
        logger.info(f"Processed refund: {refund['id']}")
        return refund
    except Exception as e:
        logger.error(f"Error processing refund: {str(e)}")
        raise ValidationError(f"Failed to process refund: {str(e)}")

def fetch_invoice(invoice_id):
    """Fetch invoice details from Razorpay"""
    try:
        invoice = razorpay_client.invoice.fetch(invoice_id)
        logger.info(f"Fetched invoice: {invoice_id}")
        return invoice
    except Exception as e:
        logger.error(f"Error fetching invoice: {str(e)}")
        raise ValidationError(f"Failed to fetch invoice: {str(e)}")