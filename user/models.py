from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils.timezone import now

# Custom User Manager
class UserManager(BaseUserManager):
    def create_user(self, consumer_no, email, password=None, **extra_fields):
        """
        Create and return a regular user with an email and password.
        """
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(consumer_no=consumer_no, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, consumer_no, email, password=None, **extra_fields):
        """
        Create and return a superuser with an email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(consumer_no, email, password, **extra_fields)

# Custom User Model
class User(AbstractBaseUser):
    
    consumer_no = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, null=False)
    email = models.EmailField(unique=True, null=False)
    phone_number = models.CharField(max_length=11, null=False, unique=True)  # Unique phone number for login
    whatsapp_number = models.CharField(max_length=11, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    cnic = models.CharField(max_length=13, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    billing_type_choices = [
        (1, 'Installments-10'),
        (2, 'Installments-15'),
        (3, 'Monthly'),
        (4, 'Yearly'),
    ]
    billing_type = models.IntegerField(choices=billing_type_choices, default=1)
    xps = models.IntegerField(default=0)

    # JWT and Verification related fields
    is_active = models.BooleanField(default=True)  # Account active/inactive status
    reset_token = models.CharField(max_length=500, null=True, blank=True)  # Token for password reset
    jwt_token = models.CharField(max_length=500, null=True, blank=True)  # Optional: Store refresh token for long sessions
    is_verified = models.BooleanField(default=False)  # Email/Phone number verification flag

    # Fields for authentication
    USERNAME_FIELD = 'consumer_no'  # We will use consumer_no as the username field
    REQUIRED_FIELDS = ['email', 'phone_number']  # Additional fields that are required for creating a user

    class Meta:
        db_table = "Users"
    
    objects = UserManager()

    
        
    def __str__(self):
        return self.name


class OTP(models.Model):
    email = models.EmailField(unique=True)
    secret = models.CharField(max_length=100)
    generated_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"OTP for {self.email} created at {self.generated_at}"


