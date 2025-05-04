from django.contrib import admin
from .models import Billing, YearlyPayments, Payments

# Register your models here.
admin.site.register(Billing)
admin.site.register(YearlyPayments)
admin.site.register(Payments)
# admin.site.register(PaymentMethod)
