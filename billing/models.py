from django.db import models
from fyp.settings import AUTH_USER_MODEL


class Billing(models.Model):
    

    bill_id = models.AutoField(primary_key=True)
    consumer_no = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE,  related_name='bills')
    bill_amount = models.DecimalField(max_digits=10, decimal_places=2)
    bill_date = models.DateField()
    due_date = models.DateField()
    arrears = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    concession = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    paid = models.BooleanField(default=False)
    def __str__(self):
        return f"Bill ID: {self.bill_id} - Consumer No: {self.consumer_no}"

class YearlyPayments(models.Model):
    yearly_id = models.AutoField(primary_key=True)
    consumer_no = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    yearly_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_balance = models.DecimalField(max_digits=10, decimal_places=2)
    last_deduction_date = models.DateField()
    refill_status = models.BooleanField(default=False)

    def __str__(self):
        return f"Yearly Payment ID: {self.yearly_id} - Consumer No: {self.consumer_no}"

class Payments(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    ]
    remarks = models.TextField(blank=True, null=True)
    payment_id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    bill_id = models.ForeignKey(Billing, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    # payment_method_id = models.ForeignKey('PaymentMethod', on_delete=models.CASCADE)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES)

    def __str__(self):
        return f"Payment ID: {self.payment_id} - User ID: {self.user_id}"

# class PaymentMethod(models.Model):
#     PAYMENT_METHOD_CHOICES = [
#         (1, 'Credit'),
#         (2, 'Digital Wallet'),
#         (3, 'Bank Transfer'),
#     ]

#     plan_id = models.AutoField(primary_key=True)
#     plan_name = models.CharField(max_length=100)
#     installment_frequency_days = models.IntegerField()
#     installment_count = models.IntegerField()

#     def __str__(self):
#         return self.plan_name
    
class UserInstallments(models.Model):
    installment_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    bill = models.ForeignKey(Billing, on_delete=models.CASCADE)
    # plan = 
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_installments = models.IntegerField(default=0)
    remaining_balance = models.DecimalField(max_digits=10, decimal_places=2)
    next_due_date = models.DateField()
    penalty = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.user.name} - Installment for Bill {self.bill_id}"

