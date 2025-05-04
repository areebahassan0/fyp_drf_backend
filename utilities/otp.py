import pyotp
import smtplib
import datetime
from django.utils.timezone import now
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from user.models import OTP  # Adjust the path to your app's location

from django.utils.timezone import make_aware
import datetime



class PewBillOTP:

    def generate_key(self, email):
        """Generate a unique key for OTP based on the email."""
        return pyotp.random_base32()

    def create_otp(self, email):
        """Creates and stores an OTP for the given email."""
        secret = self.generate_key(email)
        otp = pyotp.TOTP(secret).now()  # Generate the OTP
        # Save to the database
        print(f"Generated OTP for verification: {otp}")
        OTP.objects.update_or_create(
            email=email,
            defaults={"secret": secret, "generated_at": now()}
        )
        # Send OTP via email (this is just a print for testing)
        print(f"Generated OTP: {otp}")
        self.send_email_otp(email, otp)  # Send OTP to email
        return otp


    def validate_otp(self, email, otp):
        try:
            otp_entry = OTP.objects.get(email=email)
            time_generated = otp_entry.generated_at
            if time_generated.tzinfo is None:
                time_generated = make_aware(time_generated)
            now_time = now()

            # Log the times and secret
            # print(f"Generated at: {time_generated}, Now: {now_time}")
            print(f"Stored secret: {otp_entry.secret}, Entered OTP: {otp}")

            if now_time - time_generated > datetime.timedelta(minutes=5):
                return False, "OTP expired. Please request a new one."

            totp = pyotp.TOTP(otp_entry.secret)
            print({totp})
            user_otp = str(otp)
            if totp.verify(user_otp, valid_window=2):  # Adjust window for testing
                return True, "OTP validated successfully."
            else:
                return False, "Invalid OTP entered. Please try again."
        except OTP.DoesNotExist:
            return False, "OTP not found. Please request a new one."
        except Exception as e:
            return False, str(e)



    def send_email_otp(self, email, otp):
        """
        Sends the generated OTP to the user's email using smtplib.
        """
        my_email = 'sendsystem8@gmail.com'
        password_key = 'ydgw mibv qeon pzcn'  # Update with your actual password
        smtp_server = "smtp.gmail.com"
        smtp_port = 587

        # Format the current date
        formatted_date = datetime.date.today()

        # Create the email message
        msg = MIMEMultipart()
        msg['Subject'] = f"Your OTP Code for Signup ({formatted_date})"
        msg['From'] = my_email
        msg['To'] = email

        # Email body
        body = (
            f"Dear User,\n\n"
            f"Your OTP code for completing the signup process is: {otp}\n\n"
            f"This code will expire in 5 minutes. Please do not share it with anyone.\n\n"
            f"Best regards,\nKEnergy Link "
        )
        msg.attach(MIMEText(body, "plain"))

        try:
            # Send the email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.login(my_email, password_key)
                server.send_message(msg)
            print(f"OTP sent to {email} successfully!")
            return True
        except Exception as e:
            print(f"Error sending OTP: {str(e)}")
            return False
