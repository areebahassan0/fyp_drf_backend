from datetime import datetime, timedelta
from .models import Payments, Billing, YearlyPayments
from django.utils import timezone
from django.db import models
from django.utils.timezone import now
from .models import Billing, YearlyPayments
from user.models import User
from user.models import User
from .models import Billing, YearlyPayments, UserInstallments
from .serializers import BillingSerializer, YearlyPaymentsSerializer, InstallmentPlanSummarySerializer
from rest_framework import status
from .models import Payments
from .serializers import PaymentSerializer
from user.models import User
from datetime import datetime
from datetime import date
import random

def fetch_payment_history(user_id, start_date=None, end_date=None):
    try:
        user = User.objects.get(consumer_no=user_id)
    except User.DoesNotExist:
        return {"error": "User not found."}

    payments = Payments.objects.filter(user_id=user)
    print(payments)
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

    if user.billing_type != 2:  # Monthly
        return {"data": {"error": "User is not on Monthly billing plan."}, "status": status.HTTP_400_BAD_REQUEST}

    # Example logic for bill creation
    today = date.today()
    bill_amount = random.uniform(2000, 4000)  # Replace with actual calculation logic

    bill = Billing.objects.create(
        consumer_no=user,
        bill_amount=round(bill_amount, 2),
        bill_date=today,
        due_date=today + timedelta(days=15),
        arrears=0,
        concession=0,
        paid=False
    )

    return {
        "data": {
            "message": "Monthly bill generated.",
            "bill_id": bill.bill_id,
            "amount": bill.bill_amount,
            "due_date": bill.due_date
        },
        "status": status.HTTP_200_OK
    }

def process_bill_payment(id, data):
    try:
        user = User.objects.get(consumer_no=id)
    except User.DoesNotExist:
        return {"data": {"error": "User not found."}, "status": status.HTTP_404_NOT_FOUND}

    try:
        bill = Billing.objects.get(bill_id=data['bill_id'], consumer_no=user)
        # console.log(bill)
    except Billing.DoesNotExist:
        return {"data": {"error": "Bill not found."}, "status": status.HTTP_404_NOT_FOUND}
    # console.log(bill)
    if bill.paid:
        return {"data": {"error": "Bill is already paid."}, "status": status.HTTP_400_BAD_REQUEST}

    # try:
    #     method = PaymentMethod.objects.get(plan_id=data['payment_method_id'])
    # except PaymentMethod.DoesNotExist:
    #     return {"data": {"error": "Payment method not found."}, "status": status.HTTP_404_NOT_FOUND}

    # Optional: Deduct from Yearly Balance if yearly billing
    if user.billing_type == 3:
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
        payment_date=date.today(),
        # payment_method_id=method,
        payment_status='Completed'
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
    
    latest_unpaid = Billing.objects.filter(consumer_no=user, paid=False).order_by('-bill_date').first()
    latest_bill_serialized = BillingSerializer(latest_unpaid).data if latest_unpaid else None

    arrears = latest_unpaid.arrears if latest_unpaid else 0
    total_due = latest_unpaid.bill_amount if latest_unpaid else 0

    # Yearly billing logic
    yearly = YearlyPayments.objects.filter(consumer_no=user).first()
    yearly_data = YearlyPaymentsSerializer(yearly).data if yearly else None

    # Installment plan logic
    installment_data = None
    if user.billing_type == 1:
        installment = UserInstallments.objects.filter(user=user).order_by('-next_due_date').first()
        if installment:
            plan = installment.plan
            plan_data = InstallmentPlanSummarySerializer(plan).data
            installment_data = {
                "plan": plan_data,
                "total_amount": installment.total_amount,
                "paid_installments": installment.paid_installments,
                "remaining_balance": installment.remaining_balance,
                "next_due_date": installment.next_due_date,
                "penalty": installment.penalty
            }

    return {
        "billing_type": user.get_billing_type_display(),
        "arrears": arrears,
        "latest_unpaid_bill": latest_bill_serialized,
        "yearly_balance": yearly_data if user.billing_type == 3 else None,
        "installment_plan": installment_data if user.billing_type == 1 else None,
        "total_due": total_due
    }

def update_billing_method(user_id, new_type):
    try:
        user = User.objects.get(consumer_no=user_id)
    except User.DoesNotExist:
        return {
            "error": "User not found.",
           
        }

    valid_types = [1, 2, 3, 4]
    if int(new_type) not in valid_types:
        return {
            "data": {"error": "Invalid billing type. Choose 1 (Installments), 2 (Monthly), or 3 (Yearly-10 days) or 4(Yearly-15 days)."},
           
        }

    # Handle switching to Yearly
    if int(new_type) == 3:
        unpaid_bills = Billing.objects.filter(consumer_no=user, paid=False)
        if unpaid_bills.exists():
            total_due = sum([bill.bill_amount for bill in unpaid_bills])
            return {
                "data": {
                    "error": f"Cannot switch to Yearly. You have unpaid dues of {total_due}."
                },
                "status": status.HTTP_400_BAD_REQUEST
            }

        # Update billing_type
        user.billing_type = 3

        # OPTIONAL: Assign default plan_id or logic if needed

        # Create YearlyPayments record if not already exists
        if not YearlyPayments.objects.filter(consumer_no=user).exists():
            YearlyPayments.objects.create(
                consumer_no=user,
                yearly_amount=0.00,
                current_balance=0.00,
                last_deduction_date=now().date(),
                refill_status=False
            )

        user.save()

        return {
            "data": {"message": "Billing type updated to Yearly. You can now refill your yearly balance."},
            "status": status.HTTP_200_OK
        }

    # For Monthly or Installments
    user.billing_type = int(new_type)
    user.save()
    return {
        "data": {"message": f"Billing type updated successfully to {user.get_billing_type_display()}."},
        "status": status.HTTP_200_OK
    }
def generate_installment_bills(user_id):
    try:
        user = User.objects.get(consumer_no=user_id)
    except User.DoesNotExist:
        return {
            "data": {"error": "User not found."},
            "status": status.HTTP_404_NOT_FOUND
        }

    today = date.today()
    bills_created = []

    # Always generate a monthly bill
    monthly_amount = round(random.uniform(2500, 4000), 2)
    monthly_bill = Billing.objects.create(
        consumer_no=user,
        bill_amount=monthly_amount,
        bill_date=today,
        due_date=today + timedelta(days=15),
        arrears=0,
        concession=0,
        paid=(user.billing_type == 4)  # Auto-pay for Yearly
    )
    bills_created.append({
        "type": "monthly",
        "bill_id": monthly_bill.bill_id,
        "amount": monthly_bill.bill_amount
    })

    # Auto-deduct for Yearly
    if user.billing_type == 4:
        yearly = YearlyPayments.objects.filter(consumer_no=user).first()
        if yearly and yearly.current_balance >= monthly_amount:
            yearly.current_balance -= monthly_amount
            yearly.save()
        else:
            return {
                "data": {"error": "Insufficient yearly balance to auto-pay monthly bill."},
                "status": status.HTTP_400_BAD_REQUEST
            }

    # If installment plan (10 or 15 day)
    if user.billing_type in [1, 2]:
        frequency = 10 if user.billing_type == 1 else 15
        count = 3 if frequency == 10 else 2
        installment_amount = round(monthly_amount / count, 2)

        for i in range(count):
            inst_bill = Billing.objects.create(
                consumer_no=user,
                bill_amount=installment_amount,
                bill_date=today + timedelta(days=i * frequency),
                due_date=today + timedelta(days=i * frequency + 5),
                arrears=0,
                concession=0,
                paid=False
            )
            bills_created.append({
                "type": f"installment-{i+1}",
                "bill_id": inst_bill.bill_id,
                "amount": inst_bill.bill_amount
            })

    return {
        "data": {
            "message": "Bills generated successfully.",
            "bills": bills_created
        },
        "status": status.HTTP_200_OK
    }

def fetch_installment_plan(user_id):
    try:
        user = User.objects.get(consumer_no=user_id)
    except User.DoesNotExist:
        return {"error": "User not found."}

    if user.billing_type not in [1, 2]:
        return {"error": "User is not on an installment plan."}

    frequency = 10 if user.billing_type == 1 else 15
    count = 3 if frequency == 10 else 2

    return {
        "plan_name": f"{frequency}-day Installment Plan",
        "installment_frequency_days": frequency,
        "installment_count": count
    }
