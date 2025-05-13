from django.urls import path
from .views import (
    GetPaymentHistoryView, UserSummaryView, ChangeBillingMethodView,
    GetUnpaidBillsView, ViewBillByIdView, MakePaymentView,
    GenerateMonthlyBillView, GenerateInstallmentBillsView,
    GetInstallmentPlanView, CreatePaymentIntentView,
    CreatePaymentMethodView, ListPackagesView, SubscribeToPackageView,
    TrackDailyUsageView, GetPackageUsageView, PackageManagementView,
    GetUserPackagesView
)

urlpatterns = [
    # Payment History
    path('payment-history/', GetPaymentHistoryView.as_view(), name='payment_history'),
    
    # Billing Method Management
   path('method/', UserSummaryView.as_view(), name='get_billing_method'),
    path('method/change/', ChangeBillingMethodView.as_view(), name='change_billing_method'),
     
    # Bills Management
    path('unpaid/', GetUnpaidBillsView.as_view(), name='get_unpaid_bills'),
    path('view/<int:bill_id>/', ViewBillByIdView.as_view(), name='view_bill_by_id'),
    
    # Payment Processing
    path('pay/', MakePaymentView.as_view(), name='make_payment'),
    path('payment-method/create/', CreatePaymentMethodView.as_view(), name='create_payment_method'),
    path('create-payment-intent/', CreatePaymentIntentView.as_view(), name='create_payment_intent'),
    
    # Bill Generation
    path('generate/monthly/', GenerateMonthlyBillView.as_view(), name='generate_monthly_bill'),
    path('generate/installments/', GenerateInstallmentBillsView.as_view(), name='generate_installment_bills'),
    
    # Installment Management
    path('installments/plan/', GetInstallmentPlanView.as_view(), name='get_installment_plan'),
    
    # Package Management URLs
    path('packages/manage/', PackageManagementView.as_view(), name='manage-packages'),
    path('packages/manage/<int:package_id>/', PackageManagementView.as_view(), name='manage-package-detail'),
    
    # Package User URLs
    path('packages/', ListPackagesView.as_view(), name='list-packages'),
    path('packages/subscribe/', SubscribeToPackageView.as_view(), name='subscribe-package'),
    path('packages/usage/track/', TrackDailyUsageView.as_view(), name='track-usage'),
    path('packages/usage/', GetPackageUsageView.as_view(), name='get-package-usage'),
    path('packages/user/', GetUserPackagesView.as_view(), name='get-user-packages'),
] 