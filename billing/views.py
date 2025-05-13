from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .models import Payments, Billing, YearlyPayments, Package, BillingMethod, PaymentMethod, UserInstallments, PackageUsage, DailyUsage, PackageOverage
from .actions import fetch_payment_history, update_billing_method, fetch_unpaid_bills, get_bill_by_id, process_bill_payment, process_bill_payment, fetch_installment_plan
from django.db.models import Sum, Q
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from utilities.prediction import get_usage_prediction

from .serializers import (
    PaymentSerializer, BillingSerializer, YearlyPaymentsSerializer,
    PackageSerializer, BillingMethodSerializer, UserInstallmentsSerializer,
    BillingSummarySerializer, PaymentHistoryFilterSerializer,
    ChangeBillingMethodSerializer, CreatePaymentMethodSerializer,
    ProcessPaymentSerializer,PaymentMethodSerializer,
    PackageUsageSerializer, DailyUsageSerializer, PackageOverageSerializer, SubscribeToPackageSerializer,
    PackageManagementSerializer
)
from .actions import  fetch_user_billing_summary
from user.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from utilities.stripe import create_payment_intent
from .actions import generate_monthly_bill,generate_installment_bills
from django.utils import timezone
from datetime import timedelta

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

class ListPackagesView(APIView):
    """
    View to list all active packages
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        packages = Package.objects.filter(is_active=True)
        if not packages.exists():
            return Response({
                "status": "success",
                "message": "No active packages available",
                "data": []
            })
        
        serializer = PackageSerializer(packages, many=True)
        return Response({
            "status": "success",
            "message": f"Found {packages.count()} active packages",
            "data": serializer.data
        })

class SubscribeToPackageView(APIView):
    """
    View to subscribe a user to a package and process payment
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SubscribeToPackageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": "error",
                "message": "Invalid input data",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            package = Package.objects.get(
                id=serializer.validated_data['package_id'],
                is_active=True
            )
        except Package.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Package not found or inactive",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)

        try:
            payment_method = PaymentMethod.objects.get(
                method_id=serializer.validated_data['payment_method_id'],
                user=request.user
            )
        except PaymentMethod.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Payment method not found",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if user already has an active package
        active_package = PackageUsage.objects.filter(
            user=request.user,
            is_active=True
        ).first()

        if active_package:
            return Response({
                "status": "error",
                "message": "User already has an active package",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create payment intent
        try:
            intent = create_payment_intent(
                package.price,
                metadata={
                    "user_id": request.user.consumer_no,
                    "package_id": package.id
                }
            )
        except Exception as e:
            return Response({
                "status": "error",
                "message": f"Failed to create payment intent: {str(e)}",
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Create package subscription
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=30 * package.duration_months)

        package_usage = PackageUsage.objects.create(
            user=request.user,
            package=package,
            start_date=start_date,
            end_date=end_date
        )

        # Update billing method
        billing_method, _ = BillingMethod.objects.get_or_create(user=request.user)
        billing_method.billing_type = 'PACKAGE'
        billing_method.package = package
        billing_method.save()

        # Create payment record
        payment = Payments.objects.create(
            user_id=request.user,
            amount_paid=package.price,
            payment_method=payment_method,
            payment_status='PENDING',
            transaction_id=intent['id'],
            payment_type='PACKAGE',
            remarks=f"Package subscription: {package.name}"
        )

        return Response({
            "status": "success",
            "message": "Package subscription created successfully",
            "data": {
                "clientSecret": intent['client_secret'],
                "payment_id": payment.payment_id,
                "package_usage": PackageUsageSerializer(package_usage).data
            }
        })

class TrackDailyUsageView(APIView):
    """
    View to track daily usage for a user
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        usage_kwh = request.data.get('usage_kwh')
        if not usage_kwh:
            return Response(
                {"error": "Usage amount is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get active package usage
        package_usage = PackageUsage.objects.filter(
            user=request.user,
            is_active=True
        ).first()

        if not package_usage:
            return Response(
                {"error": "No active package found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create or update daily usage
        daily_usage, created = DailyUsage.objects.get_or_create(
            user=request.user,
            date=timezone.now().date(),
            defaults={
                'usage_kwh': usage_kwh,
                'package_usage': package_usage
            }
        )

        if not created:
            daily_usage.usage_kwh = usage_kwh
            daily_usage.save()

        # Update total usage
        package_usage.total_usage += float(usage_kwh)
        package_usage.save()

        # Check for overage
        if package_usage.total_usage > package_usage.package.voltage_included:
            overage_amount = (package_usage.total_usage - package_usage.package.voltage_included) * package_usage.package.overage_rate
            PackageOverage.objects.create(
                package_usage=package_usage,
                amount=overage_amount,
                date=timezone.now().date()
            )

        # Check if notification should be sent
        if package_usage.should_notify():
            # TODO: Implement notification sending
            package_usage.last_notification_sent = timezone.now()
            package_usage.save()

        return Response(DailyUsageSerializer(daily_usage).data)

class GetPackageUsageView(APIView):
    """
    View to get current package usage details
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        package_usage = PackageUsage.objects.filter(
            user=request.user,
            is_active=True
        ).first()

        if not package_usage:
            return Response({
                "status": "success",
                "message": "No active package found for user",
                "data": None
            })

        serializer = PackageUsageSerializer(package_usage)
        return Response({
            "status": "success",
            "message": "Active package found",
            "data": serializer.data
        })

class PackageManagementView(APIView):
    """
    View for managing packages (Create, Read, Update, Delete)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]  # Only require authentication, no admin check

    def get(self, request, package_id=None):
        """
        Get all packages or a specific package
        """
        if package_id:
            try:
                package = Package.objects.get(id=package_id)
                serializer = PackageManagementSerializer(package)
                return Response({
                    "status": "success",
                    "message": "Package found",
                    "data": serializer.data
                })
            except Package.DoesNotExist:
                return Response({
                    "status": "error",
                    "message": "Package not found",
                    "data": None
                }, status=status.HTTP_404_NOT_FOUND)
        
        packages = Package.objects.all()
        if not packages.exists():
            return Response({
                "status": "success",
                "message": "No packages available",
                "data": []
            })
        
        serializer = PackageManagementSerializer(packages, many=True)
        return Response({
            "status": "success",
            "message": f"Found {packages.count()} packages",
            "data": serializer.data
        })

    def post(self, request):
        """
        Create a new package
        """
        serializer = PackageManagementSerializer(data=request.data)
        if serializer.is_valid():
            package = serializer.save()
            return Response({
                "status": "success",
                "message": "Package created successfully",
                "data": PackageManagementSerializer(package).data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": "error",
            "message": "Invalid package data",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, package_id):
        """
        Update an existing package
        """
        try:
            package = Package.objects.get(id=package_id)
        except Package.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Package not found",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if package is in use
        active_usage = PackageUsage.objects.filter(
            package=package,
            is_active=True
        ).exists()
        
        if active_usage:
            return Response({
                "status": "error",
                "message": "Cannot modify package that is currently in use",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = PackageManagementSerializer(package, data=request.data)
        if serializer.is_valid():
            updated_package = serializer.save()
            return Response({
                "status": "success",
                "message": "Package updated successfully",
                "data": PackageManagementSerializer(updated_package).data
            })
        return Response({
            "status": "error",
            "message": "Invalid package data",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, package_id):
        """
        Delete a package
        """
        try:
            package = Package.objects.get(id=package_id)
        except Package.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Package not found",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if package is in use
        active_usage = PackageUsage.objects.filter(
            package=package,
            is_active=True
        ).exists()
        
        if active_usage:
            return Response({
                "status": "error",
                "message": "Cannot delete package that is currently in use",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        package.delete()
        return Response({
            "status": "success",
            "message": "Package deleted successfully",
            "data": None
        }, status=status.HTTP_200_OK)

class GetUserPackagesView(APIView):
    """
    View to get all packages a user has subscribed to (both active and historical)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get all package usages for the user, ordered by start date (newest first)
        package_usages = PackageUsage.objects.filter(
            user=request.user
        ).order_by('-start_date')

        if not package_usages.exists():
            return Response({
                "status": "success",
                "message": "No package subscriptions found for user",
                "data": []
            })

        # Serialize the package usages
        serializer = PackageUsageSerializer(package_usages, many=True)
        
        return Response({
            "status": "success",
            "message": f"Found {package_usages.count()} package subscriptions",
            "data": {
                "active_package": serializer.data[0] if package_usages.filter(is_active=True).exists() else None,
                "package_history": serializer.data
            }
        })
