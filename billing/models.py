from django.db import models
from fyp.settings import AUTH_USER_MODEL
from django.utils import timezone
import datetime

class Package(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    voltage_included = models.IntegerField()
    duration_months = models.IntegerField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class BillingMethod(models.Model):
    BILLING_TYPE_CHOICES = [
        ('MONTHLY', 'Monthly'),
        ('YEARLY', 'Yearly'),
        ('INSTALLMENT', 'Installment'),
        ('PACKAGE', 'Package')
    ]
    
    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    billing_type = models.CharField(max_length=20, choices=BILLING_TYPE_CHOICES)
    package = models.ForeignKey(Package, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.billing_type}"

class Billing(models.Model):
    bill_id = models.AutoField(primary_key=True)
    consumer_no = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bills')
    bill_amount = models.DecimalField(max_digits=10, decimal_places=2)
    bill_date = models.DateField()
    due_date = models.DateField(default=datetime.date.today)
    arrears = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    concession = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    paid = models.BooleanField(default=False)
    billing_method = models.ForeignKey(BillingMethod, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"Bill ID: {self.bill_id} - Consumer No: {self.consumer_no}"

class YearlyPayments(models.Model):
    yearly_id = models.AutoField(primary_key=True)
    consumer_no = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    yearly_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_balance = models.DecimalField(max_digits=10, decimal_places=2)
    last_deduction_date = models.DateField()
    refill_status = models.BooleanField(default=False)
    next_refill_date = models.DateField(default=datetime.date.today)

    def __str__(self):
        return f"Yearly Payment ID: {self.yearly_id} - Consumer No: {self.consumer_no}"

class PaymentMethod(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('CREDIT_CARD', 'Credit Card'),
        ('DIGITAL_WALLET', 'Digital Wallet'),
        ('BANK_TRANSFER', 'Bank Transfer'),
    ]

    method_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    method_type = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    is_default = models.BooleanField(default=False)
    details = models.JSONField()

    def __str__(self):
        return f"{self.user} - {self.method_type}"

class Payments(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('PENDING', 'Pending'),
    ]
    
    payment_id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    bill_id = models.ForeignKey(Billing, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(default=timezone.now)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES)
    transaction_id = models.CharField(max_length=100, unique=True, blank=True, null=True    )
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Payment ID: {self.payment_id} - User ID: {self.user_id}"

class UserInstallments(models.Model):
    INSTALLMENT_FREQUENCY_CHOICES = [
        ('15_DAYS', '15 Days'),
        ('10_DAYS', '10 Days')
    ]
    
    installment_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    bill = models.ForeignKey(Billing, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_installments = models.IntegerField(default=0)
    remaining_balance = models.DecimalField(max_digits=10, decimal_places=2)
    next_due_date = models.DateField()
    penalty = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    frequency = models.CharField(max_length=10, choices=INSTALLMENT_FREQUENCY_CHOICES, default='15_DAYS')
    total_installments = models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user} - Installment for Bill {self.bill.bill_id}"

