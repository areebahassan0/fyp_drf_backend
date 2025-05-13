from rest_framework import serializers
from .models import (
    Payments, Billing, YearlyPayments, Package, 
    BillingMethod, PaymentMethod, UserInstallments,
    PackageUsage, DailyUsage, PackageOverage
)
from django.utils import timezone

class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = ['id', 'name', 'description', 'price', 'voltage_included', 
                 'duration_months', 'overage_rate']

class PackageUsageSerializer(serializers.ModelSerializer):
    package_details = PackageSerializer(source='package', read_only=True)
    remaining_kwh = serializers.SerializerMethodField()
    overage_amount = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()

    class Meta:
        model = PackageUsage
        fields = ['id', 'package', 'package_details', 'start_date', 'end_date', 
                 'total_usage', 'is_active', 'remaining_kwh', 'overage_amount',
                 'days_remaining']

    def get_remaining_kwh(self, obj):
        return obj.get_remaining_kwh()

    def get_overage_amount(self, obj):
        return obj.get_overage_amount()

    def get_days_remaining(self, obj):
        if obj.is_active:
            return (obj.end_date - timezone.now().date()).days
        return 0

class DailyUsageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyUsage
        fields = ['id', 'user', 'date', 'usage_kwh', 'package_usage']

class PackageOverageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackageOverage
        fields = ['id', 'package_usage', 'amount', 'date', 'is_paid', 'bill']

class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ['method_id', 'method_type', 'is_default', 'details']
        extra_kwargs = {
            'details': {'write_only': True}  # Hide sensitive payment details in responses
        }

class PaymentSerializer(serializers.ModelSerializer):
    payment_method = PaymentMethodSerializer(read_only=True)
    
    class Meta:
        model = Payments
        fields = [
            'payment_id', 'user_id', 'bill_id', 'amount_paid', 
            'payment_date', 'payment_method', 'payment_status',
            'transaction_id', 'remarks'
        ]
        read_only_fields = ['payment_id', 'transaction_id']

class BillingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Billing
        fields = [
            'bill_id', 'consumer_no', 'bill_amount', 'bill_date', 
            'due_date', 'paid', 'arrears', 'concession', 'billing_method'
        ]

class YearlyPaymentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = YearlyPayments
        fields = [
            'yearly_id', 'consumer_no', 'yearly_amount', 
            'current_balance', 'last_deduction_date', 
            'refill_status', 'next_refill_date'
        ]

class UserInstallmentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserInstallments
        fields = [
            'installment_id', 'user', 'bill', 'total_amount',
            'paid_installments', 'remaining_balance', 'next_due_date',
            'penalty', 'frequency', 'total_installments', 'is_completed'
        ]

class BillingMethodSerializer(serializers.ModelSerializer):
    package = PackageSerializer(read_only=True)
    
    class Meta:
        model = BillingMethod
        fields = [
            'user', 'billing_type', 'package', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class BillingSummarySerializer(serializers.Serializer):
    billing_method = BillingMethodSerializer()
    arrears = serializers.DecimalField(max_digits=10, decimal_places=2)
    latest_unpaid_bill = BillingSerializer(required=False)
    yearly_balance = YearlyPaymentsSerializer(required=False)
    installment_plan = UserInstallmentsSerializer(required=False)
    total_due = serializers.DecimalField(max_digits=10, decimal_places=2)
    usage_prediction = serializers.DictField(required=False)

class PaymentHistoryFilterSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    status = serializers.ChoiceField(
        choices=Payments.PAYMENT_STATUS_CHOICES,
        required=False
    )

class ChangeBillingMethodSerializer(serializers.Serializer):
    billing_type = serializers.ChoiceField(choices=BillingMethod.BILLING_TYPE_CHOICES)
    package_id = serializers.IntegerField(required=False)
    frequency = serializers.ChoiceField(
        choices=UserInstallments.INSTALLMENT_FREQUENCY_CHOICES,
        required=False
    )

class CreatePaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ['method_type', 'details']
        extra_kwargs = {
            'details': {'write_only': True}
        }

class ProcessPaymentSerializer(serializers.Serializer):
    bill_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_method_id = serializers.IntegerField()
    remarks = serializers.CharField(required=False, allow_blank=True)

class SubscribeToPackageSerializer(serializers.Serializer):
    package_id = serializers.IntegerField()
    payment_method_id = serializers.IntegerField()

class PackageManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = ['id', 'name', 'description', 'price', 'voltage_included', 
                 'duration_months', 'overage_rate', 'is_active']
        
    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0")
        return value
    
    def validate_voltage_included(self, value):
        if value <= 0:
            raise serializers.ValidationError("Voltage included must be greater than 0")
        return value
    
    def validate_duration_months(self, value):
        if value <= 0:
            raise serializers.ValidationError("Duration must be greater than 0")
        return value
    
    def validate_overage_rate(self, value):
        if value < 0:
            raise serializers.ValidationError("Overage rate cannot be negative")
        return value
