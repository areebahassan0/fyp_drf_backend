from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .models import Payments, Billing, YearlyPayments, Package, BillingMethod, PaymentMethod, UserInstallments
from .actions import fetch_payment_history, update_billing_method, fetch_unpaid_bills, get_bill_by_id, process_bill_payment, process_bill_payment, fetch_installment_plan
from django.db.models import Sum, Q
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from utilities.prediction import get_usage_prediction

from .serializers import (
    PaymentSerializer, BillingSerializer, YearlyPaymentsSerializer,
    PackageSerializer, BillingMethodSerializer, UserInstallmentsSerializer,
    BillingSummarySerializer, PaymentHistoryFilterSerializer,
    ChangeBillingMethodSerializer, CreatePaymentMethodSerializer,
    ProcessPaymentSerializer,PaymentMethodSerializer
)
from .actions import  fetch_user_billing_summary
from user.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from utilities.stripe import create_payment_intent
from .actions import generate_monthly_bill,generate_installment_bills

# Decorator to ensure the user is logged in
class GetPaymentHistoryView(APIView):
    """
    View to retrieve a user's payment history, optionally filtered by date.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = PaymentHistoryFilterSerializer(data=request.GET)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        payments = Payments.objects.filter(user_id=user)

        # Apply filters
        if serializer.validated_data.get('start_date'):
            payments = payments.filter(payment_date__gte=serializer.validated_data['start_date'])
        if serializer.validated_data.get('end_date'):
            payments = payments.filter(payment_date__lte=serializer.validated_data['end_date'])
        if serializer.validated_data.get('status'):
            payments = payments.filter(payment_status=serializer.validated_data['status'])

        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)

class UserSummaryView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            print(f"user: {user}")
            billing_method = BillingMethod.objects.get(user=user)
            unpaid_bills = Billing.objects.filter(
                consumer_no=user,
                paid=False
            ).order_by('-due_date')

            # Calculate total due
            total_due = unpaid_bills.aggregate(
                total=Sum('bill_amount') + Sum('arrears')
            )['total'] or 0

            # Get yearly balance if applicable
            yearly_balance = None
            if billing_method.billing_type == 'YEARLY':
                yearly_balance = YearlyPayments.objects.filter(
                    consumer_no=user
                ).first()

            # Get installment plan if applicable
            installment_plan = None
            if billing_method.billing_type == 'INSTALLMENT':
                installment_plan = UserInstallments.objects.filter(
                    user=user,
                    is_completed=False
                ).first()
            print(f"installment plan: {installment_plan}")
            # Get usage prediction
            prediction_data = get_usage_prediction(1)
            print(f"prediction data: {prediction_data}")

            data = {
                'billing_method': billing_method,
                'arrears': sum(bill.arrears for bill in unpaid_bills),
                'latest_unpaid_bill': unpaid_bills.first() if unpaid_bills.exists() else None,
                'yearly_balance': yearly_balance,
                'installment_plan': installment_plan,
                'total_due': total_due,
                'usage_prediction': prediction_data if prediction_data else {
                    "house_id": "1",
                    "predicted_usage": 0.0,
                    "error": "Unable to fetch prediction data"
                }
            }

            serializer = BillingSummarySerializer(instance=data)
            return Response(serializer.data)

        except BillingMethod.DoesNotExist:
            return Response(
                {"error": "No billing method found for user"},
                status=status.HTTP_404_NOT_FOUND
            )

class GetUnpaidBillsView(APIView):
    """
    View to retrieve all unpaid bills for a specific user.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        unpaid_bills = Billing.objects.filter(
            consumer_no=user,
            paid=False
        ).order_by('due_date')
        
        serializer = BillingSerializer(unpaid_bills, many=True)
        return Response(serializer.data)
    
class ViewBillByIdView(APIView):
    """
    View to get the details of a single bill using its bill ID.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, bill_id):
        try:
            bill = Billing.objects.get(bill_id=bill_id, consumer_no=request.user)
            serializer = BillingSerializer(bill)
            return Response(serializer.data)
        except Billing.DoesNotExist:
            return Response(
                {"error": "Bill not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    

class MakePaymentView(APIView):
    """
    View to process a payment for a user's bill.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ProcessPaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            print(f"here")
            bill = Billing.objects.get(
                bill_id=serializer.validated_data['bill_id'],
                consumer_no=request.user
            )
            print(f"bill:", bill)
            if not bill:
                return Response({"error": "Bill not found"}, status=status.HTTP_404_NOT_FOUND)
            print(f"bill found")
            try:
                payment_method = PaymentMethod.objects.get(
                    method_id=serializer.validated_data['payment_method_id'],
                    user=request.user
                )
                print(f"Payment method found: {payment_method.method_id}")
            except PaymentMethod.DoesNotExist:
                return Response(
                    {"error": f"Payment method with ID {serializer.validated_data['payment_method_id']} not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Create payment intent with Stripe
            print(f"Payment amount: {serializer.validated_data['amount']}")
            intent = create_payment_intent(
                serializer.validated_data['amount'],
                metadata={
                    "user_id": request.user.consumer_no,
                    "bill_id": bill.bill_id
                }
            )

            # Create payment record
            payment = Payments.objects.create(
                user_id=request.user,
                bill_id=bill,
                amount_paid=serializer.validated_data['amount'],
                payment_method=payment_method,
                payment_status='PENDING',
                transaction_id=intent['id'],
                remarks=serializer.validated_data.get('remarks', '')
            )

            return Response({
                "clientSecret": intent['client_secret'],
                "payment_id": payment.payment_id
            })

        except (Billing.DoesNotExist, PaymentMethod.DoesNotExist):
            return Response(
                {"error": "Bill or payment method not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class GenerateMonthlyBillView(APIView):
    """
    View to manually generate a monthly bill for a user.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user  # DRF sets this from the JWT
        user_id = user.consumer_no 
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        result = generate_monthly_bill(user_id)

        if result["status"] == 200:
            return Response(result["data"], status=status.HTTP_200_OK)
        else:
            return Response(result["data"], status=result["status"])

class GenerateInstallmentBillsView(APIView):
    """
    Generate bills for a user based on installment frequency (10 or 15 days) along with the monthly bill.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user  # DRF sets this from the JWT
        user_id = user.consumer_no
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        result = generate_installment_bills(user_id)

        if result["status"] == 200:
            return Response(result["data"], status=status.HTTP_200_OK)
        else:
            return Response(result["data"], status=result["status"])

class GetInstallmentPlanView(APIView):
    """
    View to fetch the installment plan of a user.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        installment_plans = UserInstallments.objects.filter(
            user=user,
            is_completed=False
        ).order_by('next_due_date')
        if not installment_plans:
            return Response({"error": "No installment plan found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserInstallmentsSerializer(installment_plans, many=True)
        return Response(serializer.data)


class ChangeBillingMethodView(APIView):
    """
    View to change the billing method of a user to Monthly, Installments, or Yearly.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        serializer = ChangeBillingMethodSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        billing_type = serializer.validated_data['billing_type']

        # Check for unpaid bills
        if Billing.objects.filter(consumer_no=user, paid=False).exists():
            return Response(
                {"error": "Cannot change billing method with unpaid bills"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            billing_method = BillingMethod.objects.get(user=user)
            billing_method.billing_type = billing_type

            if billing_type == 'PACKAGE':
                package_id = serializer.validated_data.get('package_id')
                if not package_id: 
                    return Response(
                        {"error": "Package ID required for package billing"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                billing_method.package_id = package_id

            billing_method.save()

            # Handle installment frequency if applicable
            if billing_type == 'INSTALLMENT':
                frequency = serializer.validated_data.get('frequency')
                if not frequency:
                    return Response(
                        {"error": "Frequency required for installment billing"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            return Response(BillingMethodSerializer(billing_method).data)

        except BillingMethod.DoesNotExist:
            # Create new billing method
            billing_method = BillingMethod.objects.create(
                user=user,
                billing_type=billing_type,
                package_id=serializer.validated_data.get('package_id')
            )
            return Response(
                BillingMethodSerializer(billing_method).data,
                status=status.HTTP_201_CREATED
            )

class CreatePaymentMethodView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreatePaymentMethodSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        payment_method = PaymentMethod.objects.create(
            user=request.user,
            **serializer.validated_data
        )

        return Response(
            PaymentMethodSerializer(payment_method).data,
            status=status.HTTP_201_CREATED
        )

class CreatePaymentIntentView(APIView):
    """
    View to create a Stripe payment intent for processing payments.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        amount = request.data.get('amount')
        if not amount:
            return Response(
                {"error": "Amount is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Create payment intent with Stripe
            intent = create_payment_intent(
                amount=amount,
                metadata={
                    "user_id": request.user.consumer_no,
                    "email": request.user.email
                }
            )
            
            return Response({
                "clientSecret": intent['client_secret'],
                "paymentIntentId": intent['id']
            })
            
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
