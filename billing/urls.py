from django.urls import path
from .views import GetPaymentHistoryView,  UserSummary, ChangeBillingMethodView, GetUnpaidBillsView,ViewBillByIdView, MakePaymentView, GenerateMonthlyBillView, GenerateInstallmentBillsView, GetInstallmentPlanView, CreatePaymentIntentView

urlpatterns = [
    path('payment-history/', GetPaymentHistoryView.as_view(), name='payment_history'),
    
    path('method/',  UserSummary.as_view(), name='get_billing_method'),
    path('method/change/', ChangeBillingMethodView.as_view(), name='change_billing_method'),
    path('unpaid/', GetUnpaidBillsView.as_view(), name='get_unpaid_bills'),
    path('view/', ViewBillByIdView.as_view(), name='view_bill_by_id'),
    path('pay/', MakePaymentView.as_view(), name='make_payment'),
    path('generate/monthly/', GenerateMonthlyBillView.as_view(), name='generate_monthly_bill'),
    path('generate/installments/', GenerateInstallmentBillsView.as_view(), name='generate_installment_bills'),
    path('installments/plan/', GetInstallmentPlanView.as_view(), name='get_installment_plan'),
    path('create-payment-intent/', CreatePaymentIntentView.as_view(), name='create-payment-intent'),

] 