from user.models import User
from user.models import OTP

class UserQueries:
    @staticmethod
    def get_user_by_email(email):
        try:
            
            # Case-insensitive search for the email
            user = User.objects.get(email__iexact=email)
            
            return user
        except User.DoesNotExist:
            return None

    @staticmethod
    def check_email_exists(email):
        """
        Checks if an email address already exists.
        """
        return User.objects.filter(email=email).exists()

    @staticmethod
    def check_cnic_exists(cnic):
        """
        Checks if a CNIC already exists.
        """
        return User.objects.filter(cnic=cnic).exists()

    @staticmethod
    def create_user(data):
        """
        Create a user with the provided data.
        """
        return User.objects.create(
            email=data['email'],
            password=data['password'],
            name=data['name'],
            phone_number=data['phone_number'],
            address=data['address'],
            cnic=data['cnic'],
        )
   
    
    @staticmethod
    def get_otp_for_email(email):
        """
        Retrieve OTP object for a given email.
        """
        try:
            return OTP.objects.get(email=email)
        except OTP.DoesNotExist:
            return None