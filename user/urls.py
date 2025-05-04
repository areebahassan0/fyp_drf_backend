from django.urls import path
from user.views import UserSignup,VerifyOTPView,LoginView,ForgetPasswordView,OTPVerifyForgetPasswordView,ChangePasswordView,LogoutView,SendOTPView

urlpatterns = [
    path('signup/', UserSignup.as_view(), name='signup'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('send-otp/', SendOTPView.as_view(), name='send-otp'),
    path('login/', LoginView.as_view(), name='login'),
    path('forget-password/', ForgetPasswordView.as_view(), name='forget-password'),
    path('forget-password-otp/', OTPVerifyForgetPasswordView.as_view(), name='forget-password-otp-verify'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('logout/', LogoutView.as_view(), name='logout'),
]

