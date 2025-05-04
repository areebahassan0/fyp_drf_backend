from rest_framework import serializers
from .models import Payments, Billing, YearlyPayments

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payments
        fields = ['payment_id', 'user_id', 'bill_id', 'amount_paid', 'payment_date', 'payment_method_id', 'payment_status']

class BillingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Billing
        fields = ['bill_id', 'consumer_no', 'bill_amount', 'bill_date', 'due_date', 'paid', 'arrears', 'concession']

class YearlyPaymentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = YearlyPayments
        fields = ['yearly_id', 'consumer_no', 'yearly_amount', 'current_balance', 'last_deduction_date', 'refill_status']


class InstallmentPlanSummarySerializer(serializers.Serializer):
    plan_name = serializers.CharField()
    installment_frequency_days = serializers.IntegerField()
    installment_count = serializers.IntegerField()

class BillingSummarySerializer(serializers.Serializer):
    billing_type = serializers.CharField()
    arrears = serializers.DecimalField(max_digits=10, decimal_places=2)
    latest_unpaid_bill = BillingSerializer()
    yearly_balance = YearlyPaymentsSerializer(required=False)
    installment_plan = InstallmentPlanSummarySerializer(required=False)
    total_due = serializers.DecimalField(max_digits=10, decimal_places=2)
