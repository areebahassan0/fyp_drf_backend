from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .models import Payments, Billing
from .actions import fetch_payment_history, update_billing_method, fetch_unpaid_bills, get_bill_by_id, process_bill_payment, process_bill_payment, fetch_installment_plan
from django.db.models import Sum
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from .serializers import BillingSummarySerializer
from .actions import  fetch_user_billing_summary
from user.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from utilities.stripe import create_payment_intent
from .actions import generate_monthly_bill

# Decorator to ensure the user is logged in
class GetPaymentHistoryView(APIView):
    """
    View to retrieve a user's payment history, optionally filtered by date.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user  # DRF sets this from the JWT
        user_id = user.consumer_no 
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        if not user_id:
            return Response.error({"description": "User ID is required."}, status=400)

        result = fetch_payment_history(user_id, start_date, end_date)

        if isinstance(result, dict) and result.get("error"):
            return Response.error({"description": result["error"]}, status=404)


        return Response(result)
 
class UserSummary(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user  # DRF sets this from the JWT
        user_id = user.consumer_no  # or user.consumer_no if you're using that as the ID
        
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        summary = fetch_user_billing_summary(user_id)
        
        if summary.get("error"):
            return Response(summary, status=status.HTTP_404_NOT_FOUND)
        
        return Response(summary, status=status.HTTP_200_OK)

class GetUnpaidBillsView(APIView):
    """
    View to retrieve all unpaid bills for a specific user.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user  # DRF sets this from the JWT
        user_id = user.consumer_no
        if not user_id:
            return Response.error({"description": "User ID is required."}, status=400)

        result = fetch_unpaid_bills(user_id)

        if isinstance(result, dict) and result.get("error"):
            return Response.error({"description": result["error"]}, status=404)

        return Response(result)
    
class ViewBillByIdView(APIView):
    """
    View to get the details of a single bill using its bill ID.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        bill_id = request.GET.get('bill_id')
        if not bill_id:
            return Response({"description": "bill_id is required."}, status=400)

        result = get_bill_by_id(bill_id)

        if isinstance(result, dict) and result.get("error"):
            return Response.error({"description": result["error"]}, status=404)

        return Response(result)
    

class MakePaymentView(APIView):
    """
    View to process a payment for a user's bill.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        user = request.user  # DRF sets this from the JWT
        user_id = user.consumer_no 
        required_fields = ['user_id', 'bill_id', 'amount', 'payment_method_id']

        for field in required_fields:
            if field not in data:
                return Response({"description": f"{field} is required."}, status=400)

        result = process_bill_payment(user_id,data)

        if result["status"] == 200:
            return Response.success_data(result["data"])
        else:
            return Response(result["data"], status=result["status"])


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
            return Response.error({"description": "User ID is required."}, status=400)

        result = generate_monthly_bill(user_id)

        if result["status"] == 200:
            return Response.success_data(result["data"])
        else:
            return Response(result["data"], status=result["status"])
from .actions import generate_installment_bills

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
            return Response({"description": "User ID is required."}, status=400)

        result = generate_installment_bills(user_id)

        if result["status"] == 200:
            return Response.success_data(result["data"])
        else:
            return Response(result["data"], status=result["status"])
    from .actions import fetch_installment_plan

class GetInstallmentPlanView(APIView):
    """
    View to fetch the installment plan of a user.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user  # DRF sets this from the JWT
        user_id = user.consumer_no 
        if not user_id:
            return Response.error({"description": "User ID is required."}, status=400)

        result = fetch_installment_plan(user_id)

        if result.get("error"):
            return Response.error({"description": result["error"]}, status=404)

        return Response.success_data(result)


class ChangeBillingMethodView(APIView):
    """
    View to change the billing method of a user to Monthly, Installments, or Yearly.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user = request.user  # DRF sets this from the JWT
        user_id = user.consumer_no 
        billing_type = request.data.get('billing_type')

        if not user_id or billing_type is None:
            return Response({
                "description": "User ID and billing_type are required."
            }, status=400)

        result = update_billing_method(user_id, billing_type)

        if result["status"] == 200:
            
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result["data"], status=result["status"])
        
class CreatePaymentIntentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        amount = request.data.get("amount")
        if not amount:
            return Response({"error": "Amount is required"}, status=400)

        intent = create_payment_intent(amount, metadata={"user_id": request.user.consumer_nof})
        return Response({
            "clientSecret": intent['client_secret']
        })
