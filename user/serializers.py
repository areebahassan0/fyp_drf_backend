from rest_framework import serializers
from user.models import User
from user.queries import UserQueries
import re
from django.contrib.auth import authenticate
from utilities.otp import PewBillOTP
from rest_framework_simplejwt.tokens import RefreshToken

class SignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'first_name', 
            'last_name', 
            'email', 
            'phone_number', 
            'whatsapp_number', 
            'cnic', 
            'address', 
            'password'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate_cnic(self, value):
        """
        Validates CNIC to ensure it is a unique 13-digit number.
        """
        if not re.match(r'^\d{13}$', value):
            raise serializers.ValidationError("CNIC must be a unique 13-digit number.")
        if UserQueries.check_cnic_exists(value):
            raise serializers.ValidationError("CNIC already exists.")
        return value

    def validate_email(self, value):
        """
        Validates that the email is unique.
        """
        if UserQueries.check_email_exists(value):
            raise serializers.ValidationError("Email already exists.")
        return value


class SendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User does not exist.")
        return value


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()  # Validate the email field
    otp = serializers.CharField()  # Define OTP as a CharField (or IntegerField based on your implementation)

    # def validate(self, data):
    #     """
    #     Custom validation to ensure the email and OTP are in the correct format.
    #     """
    #     email = data.get('email')
    #     otp = data.get('otp')

    #     # Example: Check if email exists in the database
    #     if not UserQueries.check_email_exists(email):  # Changed this to check for non-existence
    #         raise serializers.ValidationError({"email": "This email is not registered."})

    #     # Further validations (if needed) can go here
    #     return data
  

class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField(required=True)  # Consumer number or CNIC
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        identifier = data.get('identifier')
        password = data.get('password')

        if not identifier or not password:
            raise serializers.ValidationError("Both identifier and password are required.")

        # Authenticate using consumer_no or CNIC
        user = User.objects.filter(consumer_no=identifier).first() or \
               User.objects.filter(cnic=identifier).first()

        if not user or not user.check_password(password):
            raise serializers.ValidationError("Invalid credentials. Please try again.")

        if not user.is_active:
            raise serializers.ValidationError("This account is inactive. Please contact support.")

        data['user'] = user
        return data
    
class ForgetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        """
        Validate that the email exists in the database.
        """
        from user.models import User
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Email not found.")
        return value

class OTPVerifyForgetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

    # def validate(self, data):
    #     """
    #     Validate the OTP and email combination.
    #     """
    #     from user.models import OTP
    #     email = data.get('email')
    #     otp = data.get('otp')
    #     print(otp)
    #     # Initialize the OTP handler
    #     otp_handler = PewBillOTP()
        
    #     # Validate the OTP
    #     is_valid, message = otp_handler.validate_otp(email, otp)
        
    #     if not is_valid:
    #         raise serializers.ValidationError({"otp": message})
        
    #     return data
from django.contrib.auth.password_validation import validate_password

class ChangePasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')
        if new_password != confirm_password:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "User not found."})

        # Check if the new password matches the old password
        if user.check_password(new_password):
            raise serializers.ValidationError({"new_password": "New password cannot be the same as the old password."})
        return attrs

class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()

    def validate(self, attrs):
        refresh_token = attrs.get("refresh_token")

        try:
            # Blacklist the refresh token
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception as e:
            raise serializers.ValidationError({"detail": "Invalid or expired token."})

        return attrs