from rest_framework.views import APIView
from user.actions import signup_action
from fyp.responses import Response
from fyp.responsesdescription import INVALID_DATA
from user.actions import verify_otp_action # Import the action to verify OTP
from user.serializers import VerifyOTPSerializer 
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny  # Add this import
from user.actions import signup_action
from fyp.responses import Response
from fyp.responsesdescription import INVALID_DATA
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from user.serializers import LoginSerializer
from user.actions import login_action
from fyp.responses import Response
from rest_framework import status
from user.serializers import ForgetPasswordSerializer
from user.actions import send_otp_for_password_reset,change_password_action,send_otp_action
from user.serializers import OTPVerifyForgetPasswordSerializer, ChangePasswordSerializer,LogoutSerializer,SendOTPSerializer
from user.actions import verify_otp_action
from rest_framework.permissions import IsAuthenticated

class UserSignup(APIView):
    """
    View for handling user signup.
    """
    permission_classes = [AllowAny]  # Allow unrestricted access

    @staticmethod
    def post(request):
        try:
            if request.data:
                return signup_action(data=request.data)  # Call the signup action
            else:
                return Response.error(INVALID_DATA)
        except Exception as err:
            return Response.error(str(err))


class SendOTPView(APIView):
    """
    API View to handle sending OTP to a user's email.
    """
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            return send_otp_action(email)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        
class VerifyOTPView(APIView):
    """
    View for verifying OTP during signup.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            # Validate incoming data using the serializer
            serializer = VerifyOTPSerializer(data=request.data)
            if serializer.is_valid():
                # Call the action to verify OTP
                return verify_otp_action(**serializer.validated_data)
            else:
                # If validation fails
                return Response.error(INVALID_DATA)
        except Exception as err:
            return Response.error(str(err))


class LoginView(APIView):
    """
    View for user login and token generation.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            result = login_action(data)
            return Response.success_data(result)
        else:
            return Response.error_login({"description": "Invalid data.", "errors": serializer.errors}, status=400)


class ForgetPasswordView(APIView):
    """
    View to handle forget password functionality.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        # Deserialize the request data
        serializer = ForgetPasswordSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data.get('email')

            # Call the action to send OTP
            otp = send_otp_for_password_reset(email)

            return Response.success({"description": "OTP sent to your email address."})
        else:
            return Response.error_login({"description": "Invalid email address."}, status=400)
        
class OTPVerifyForgetPasswordView(APIView):
    """
    View to handle OTP verification for forget password.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        # Deserialize and validate the input data
        serializer = OTPVerifyForgetPasswordSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data.get('email')
            otp = serializer.validated_data.get('otp')

            # Use the existing action for OTP verification
            return verify_otp_action(email, otp)
        return Response.error({"description": "Invalid data.", "errors": serializer.errors}, status=400)

class ChangePasswordView(APIView):
    """
    View to handle password change.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get("email")
            new_password = serializer.validated_data.get("new_password")
            return change_password_action(email, new_password)
        else:
            return Response.error({"description": "Invalid data.", "errors": serializer.errors}, status=400)
        
class LogoutView(APIView):
    """
    API to handle user logout by blacklisting their refresh token.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        if serializer.is_valid():
            return Response.success({"description": "User logged out successfully."})
        return Response.error(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
