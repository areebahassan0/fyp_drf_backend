import logging
from user.queries import UserQueries
from django.contrib.auth.hashers import make_password
from utilities.otp import PewBillOTP
from fyp.responsesdescription import OTP_SENT_ON_EMAIl, USER_ALREADY_EXISTS, TRY_AGAIN,INVALID_DATA
from fyp.responses import Response
from .models import User, OTP 
from utilities.pewbill_jwt import PewBillJWT
from fyp.responses import Response, ERROR_STATUS_CODE_CONFLICT, ERROR_STATUS_CODE_FORBIDDEN, SUCCESS_STATUS_CODE, \
    ERROR_STATUS_CODE, ERROR_STATUS_CODE_NOT_FOUND,INTERNAL_SERVER_ERROR_STATUS_CODE
from utilities.pewbill_jwt import PewBillJWT
from user.serializers import VerifyOTPSerializer,LogoutSerializer
from utilities.otp import PewBillOTP
from fyp.responsesdescription import TRY_AGAIN, OTP_SENT_ON_EMAIl
from fyp.responses import Response
from user.queries import UserQueries
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
# Initialize a logger
logger = logging.getLogger(__name__)

def signup_action(data):
    """
    Handles the signup process:
    - Validates email and CNIC uniqueness
    - Hashes the password
    - Creates a user
    - Generates an OTP and sends it to the user's email
    """
    try:
        # Check if email exists
        if UserQueries.check_email_exists(data['email']):
            
            return Response({"description": "User Already Exists."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if CNIC exists
        if UserQueries.check_cnic_exists(data['cnic']):
            return Response({"description":"CNIC already exists."}, status=status.HTTP_400_BAD_REQUEST)
            

        # Hash the password
        data['password'] = make_password(data['password'])

        # Combine first_name and last_name into 'name'
        data['name'] = f"{data.pop('first_name')} {data.pop('last_name')}"

        if 'billing_type' not in data:
            data['billing_type'] = 2  # Default billing type (Installments) 

        # Create the user
        user = UserQueries.create_user(data)

        # otp_handler = PewBillOTP()
        # otp = otp_handler.create_otp(data['email'])

        # # Store OTP secret somewhere securely, for example in a database or cache

        # # Send OTP to the user's email
        # otp_handler.send_email_otp(data['email'], otp)

        # Normally, send the OTP to the email here
        # Uncomment the following line after configuring email settings
        # otp_handler.send_email_otp(user.email, otp)

        return Response({"description":"Account Succesfully Created. Verify OTP Now"}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Signup action failed: {str(e)}", exc_info=True)
        return Response.error(TRY_AGAIN)

def send_otp_action(email):
    """
    Handles sending an OTP to the provided email address.
    - Generates an OTP
    - Sends it to the user's email
    """
    try:
        # Check if email exists in the User model
        if not UserQueries.check_email_exists(email):
            return Response({"description": "User does not exist."}, status=status.HTTP_404_NOT_FOUND)

        otp_handler = PewBillOTP()
        otp = otp_handler.create_otp(email)

        # Send OTP to the user's email
        otp_handler.send_email_otp(email, otp)

        return Response({"description": "OTP sent successfully."}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Send OTP action failed: {str(e)}", exc_info=True)
        return Response.error(TRY_AGAIN)

def send_otp_for_signup(email):
    """
    This action generates an OTP for the provided email and sends it.
    """
    user = User.objects.get(email=email)
    otp_handler = PewBillOTP()
    otp = otp_handler.create_otp(email)
    otp_handler.send_email_otp(email, otp)
    return otp


from rest_framework.response import Response
from rest_framework import status

def verify_otp_action(email, otp):
    """
    Handles OTP verification.
    """
    try:
        otp_handler = PewBillOTP()
        is_valid, message = otp_handler.validate_otp(email, otp)

        if is_valid:
            user = User.objects.get(email=email)

            if user.is_verified:
                # Create JWT tokens for login
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)
                return Response(
                    {
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "description": "Login successful.",
                        "user": {
                            "consumer_no": user.consumer_no,
                            "name": user.name,
                            "email": user.email,
                        },
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                user.is_verified = True
                user.save()
                return Response(
                    {"description": "OTP verified successfully."},
                    status=status.HTTP_200_OK,
                )
        else:
            return Response({"description": message}, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        return Response({"description": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"description": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from utilities.pewbill_jwt import PewBillJWT

def login_action(data):
    """
    Handle user login and JWT token creation.
    """
    user = data['user']
    if not user.is_verified:
        return {
            "error": "User is not verified. Please complete OTP verification.",
            "description": "Login failed."
        }
    
    jwt_handler = PewBillJWT()
    access_token, refresh_token = jwt_handler.create_jwt(user)

    # Update the user's JWT token field if needed
    user.jwt_token = refresh_token
    user.save()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "description": "Login successful.",
        "user": {
            "consumer_no": user.consumer_no,
            "name": user.name,
            "email": user.email,
        }
    }
def send_otp_for_password_reset(email):
    """
    This action generates an OTP for the provided email and sends it.
    """
    user = User.objects.get(email=email)
    otp_handler = PewBillOTP()
    otp = otp_handler.create_otp(email)
    return otp
from django.contrib.auth.hashers import make_password

def change_password_action(email, new_password):
    """
    Changes the password for a user identified by their email.
    """
    try:
        user = User.objects.get(email=email)
        
        user.password = make_password(new_password)  # Hash the password
        user.save()
        return Response({"description": "Password updated successfully."})
    except User.DoesNotExist:
        return Response({"description": "User not found."}, status=404)
    except Exception as e:
        return Response({"description": str(e)}, status=500)
