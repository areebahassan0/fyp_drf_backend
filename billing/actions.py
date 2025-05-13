from datetime import datetime, timedelta, date
from django.utils.timezone import now
from user.models import User
from .models import (
    Billing, YearlyPayments, UserInstallments, Payments,
    BillingMethod, Package, PaymentMethod
)
from .serializers import (
    BillingSerializer, YearlyPaymentsSerializer, PaymentSerializer,
    UserInstallmentsSerializer, BillingMethodSerializer, PackageSerializer
)
from rest_framework import status
import random

def fetch_payment_history(user_id, start_date=None, end_date=None):
    try:
        user = User.objects.get(consumer_no=user_id)
    except User.DoesNotExist:
        return {"error": "User not found."}

    payments = Payments.objects.filter(user_id=user)
    if not payments.exists():
        return {"message": "No payments found."}
    
    if start_date:
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            payments = payments.filter(payment_date__gte=start_date)
        except ValueError:
            return {"error": "Invalid start_date format. Use YYYY-MM-DD."}

    if end_date:
        try:
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            payments = payments.filter(payment_date__lte=end_date)
        except ValueError:
            return {"error": "Invalid end_date format. Use YYYY-MM-DD."}

    payments = payments.order_by('-payment_date')
    return PaymentSerializer(payments, many=True).data

def fetch_unpaid_bills(user_id):
    try:
        user = User.objects.get(consumer_no=user_id)
    except User.DoesNotExist:
        return {"error": "User not found."}

    unpaid_bills = Billing.objects.filter(consumer_no=user, paid=False).order_by('-bill_date')
    if not unpaid_bills.exists():
        return {"message": "No Unpaid bills found."}
    return BillingSerializer(unpaid_bills, many=True).data

def get_bill_by_id(bill_id):
    try:
        bill = Billing.objects.get(bill_id=bill_id)
    except Billing.DoesNotExist:
        return {"error": "Bill not found."}

    return BillingSerializer(bill).data

def generate_monthly_bill(user_id):
    try:
        user = User.objects.get(consumer_no=user_id)
    except User.DoesNotExist:
        return {"data": {"error": "User not found."}, "status": status.HTTP_404_NOT_FOUND}

    try:
        billing_method = BillingMethod.objects.get(user=user, billing_type='MONTHLY')
    except BillingMethod.DoesNotExist:
        return {"data": {"error": "User is not on Monthly billing plan."}, "status": status.HTTP_400_BAD_REQUEST}

    today = date.today()
    bill_amount = random.uniform(2000, 4000)  # Replace with actual calculation logic

    bill = Billing.objects.create(
        consumer_no=user,
        bill_amount=round(bill_amount, 2),
        bill_date=today,
        due_date=today + timedelta(days=15),
        arrears=0,
        concession=0,
        paid=False,
        billing_method=billing_method
    )

    return {
        "data": {
            "message": "Monthly bill generated.",
            "bill_id": bill.bill_id,
            "amount": bill.bill_amount,
            "due_date": bill.due_date,
            "consumer_no": bill.consumer_no,
            "bill_date": bill.bill_date
        },
        "status": status.HTTP_200_OK
    }

def process_bill_payment(user_id, data):
    try:
        user = User.objects.get(consumer_no=user_id)
    except User.DoesNotExist:
        return {"data": {"error": "User not found."}, "status": status.HTTP_404_NOT_FOUND}

    try:
        bill = Billing.objects.get(bill_id=data['bill_id'], consumer_no=user)
    except Billing.DoesNotExist:
        return {"data": {"error": "Bill not found."}, "status": status.HTTP_404_NOT_FOUND}

    if bill.paid:
        return {"data": {"error": "Bill is already paid."}, "status": status.HTTP_400_BAD_REQUEST}

    try:
        payment_method = PaymentMethod.objects.get(
            method_id=data['payment_method_id'],
            user=user
        )
    except PaymentMethod.DoesNotExist:
        return {"data": {"error": "Payment method not found."}, "status": status.HTTP_404_NOT_FOUND}

    # Handle yearly billing
    if bill.billing_method.billing_type == 'YEARLY':
        yearly = YearlyPayments.objects.filter(consumer_no=user).first()
        if not yearly or yearly.current_balance < float(data['amount']):
            return {"data": {"error": "Insufficient yearly balance."}, "status": status.HTTP_400_BAD_REQUEST}
        yearly.current_balance -= float(data['amount'])
        yearly.save()

    # Mark bill as paid
    bill.paid = True
    bill.save()

    # Create payment entry
    payment = Payments.objects.create(
        user_id=user,
        bill_id=bill,
        amount_paid=data['amount'],
        payment_date=now(),
        payment_method=payment_method,
        payment_status='COMPLETED',
        transaction_id=data.get('transaction_id', ''),
        remarks=data.get('remarks', '')
    )

    return {
        "data": {
            "message": "Payment successful.",
            "payment_id": payment.payment_id
        },
        "status": status.HTTP_200_OK
    }

def fetch_user_billing_summary(user_id):
    try:
        user = User.objects.get(consumer_no=user_id)
    except User.DoesNotExist:
        return {"error": "User not found."}
    
    try:
        billing_method = BillingMethod.objects.get(user=user)
    except BillingMethod.DoesNotExist:
        return {"error": "No billing method found for user."}

    latest_unpaid = Billing.objects.filter(
        consumer_no=user, 
        paid=False
    ).order_by('-bill_date').first()
    
    latest_bill_serialized = BillingSerializer(latest_unpaid).data if latest_unpaid else None
    arrears = latest_unpaid.arrears if latest_unpaid else 0
    total_due = latest_unpaid.bill_amount if latest_unpaid else 0

    # Yearly billing data
    yearly_data = None
    if billing_method.billing_type == 'YEARLY':
        yearly = YearlyPayments.objects.filter(consumer_no=user).first()
        yearly_data = YearlyPaymentsSerializer(yearly).data if yearly else None

    # Installment plan data
    installment_data = None
    if billing_method.billing_type == 'INSTALLMENT':
        installment = UserInstallments.objects.filter(
            user=user,
            is_completed=False
        ).order_by('-next_due_date').first()
        installment_data = UserInstallmentsSerializer(installment).data if installment else None

    return {
        "billing_method": BillingMethodSerializer(billing_method).data,
        "arrears": arrears,
        "latest_unpaid_bill": latest_bill_serialized,
        "yearly_balance": yearly_data,
        "installment_plan": installment_data,
        "total_due": total_due
    }

def update_billing_method(user_id, new_type):
    try:
        user = User.objects.get(consumer_no=user_id)
    except User.DoesNotExist:
        return {"error": "User not found."}

    # Check for unpaid bills
    if Billing.objects.filter(consumer_no=user, paid=False).exists():
        return {"error": "Cannot change billing method with unpaid bills."}

    try:
        billing_method = BillingMethod.objects.get(user=user)
        billing_method.billing_type = new_type
        billing_method.save()
    except BillingMethod.DoesNotExist:
        billing_method = BillingMethod.objects.create(
            user=user,
            billing_type=new_type
        )

    return {
        "message": "Billing method updated successfully.",
        "billing_method": BillingMethodSerializer(billing_method).data
    }

def generate_installment_bills(user_id):
    try:
        user = User.objects.get(consumer_no=user_id)
    except User.DoesNotExist:
        return {"data": {"error": "User not found."}, "status": status.HTTP_404_NOT_FOUND}

    try:
        billing_method = BillingMethod.objects.get(user=user, billing_type='INSTALLMENT')
    except BillingMethod.DoesNotExist:
        return {"data": {"error": "User is not on Installment billing plan."}, "status": status.HTTP_400_BAD_REQUEST}

    # Get active installment plan
    installment = UserInstallments.objects.filter(
        user=user,
        is_completed=False
    ).first()

    if not installment:
        return {"data": {"error": "No active installment plan found."}, "status": status.HTTP_400_BAD_REQUEST}

    # Create new bill for next installment
    today = date.today()
    installment_amount = installment.remaining_balance / (installment.total_installments - installment.paid_installments)

    bill = Billing.objects.create(
        consumer_no=user,
        bill_amount=round(installment_amount, 2),
        bill_date=today,
        due_date=today + timedelta(days=15 if installment.frequency == '15_DAYS' else 10),
        arrears=0,
        concession=0,
        paid=False,
        billing_method=billing_method
    )

    return {
        "data": {
            "message": "Installment bill generated.",
            "bill_id": bill.bill_id,
            "amount": bill.bill_amount,
            "due_date": bill.due_date
        },
        "status": status.HTTP_200_OK
    }

def fetch_installment_plan(user_id):
    try:
        user = User.objects.get(consumer_no=user_id)
    except User.DoesNotExist:
        return {"error": "User not found."}

    installment = UserInstallments.objects.filter(
        user=user,
        is_completed=False
    ).order_by('-next_due_date').first()

    if not installment:
        return {"error": "No active installment plan found."}

    return UserInstallmentsSerializer(installment).data
