from django.db import models
from user.models import User
from fyp.settings import AUTH_USER_MODEL
# class User(models.Model):
#     consumer_no = models.AutoField(primary_key=True)  # Auto-incrementing field
#     name = models.CharField(max_length=255, null=False)
#     email = models.EmailField(unique=True, null=False)
#     phone_number = models.CharField(max_length=11, null=False)
#     whatsapp_number = models.CharField(max_length=11, null=True, blank=True)
#     address = models.TextField(null=True, blank=True)
#     cnic = models.CharField(max_length=13, null=False)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     billing_type_choices = [
#         (1, 'Installments'),
#         (2, 'Monthly'),
#         (3, 'Yearly'),
#     ]
#     billing_type = models.IntegerField(choices=billing_type_choices, null=False)
#     xps = models.IntegerField(default=0)

#     def __str__(self):
#         return f"{self.name} ({self.consumer_no})"

class Category(models.Model):
    name = models.CharField(max_length=255, unique=True, null=False)  # Category name

    class Meta:
        db_table = "Category"
    def __str__(self):
        return self.name

    

class SubCategory(models.Model):
    # ForeignKey to Category table
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='subcategories')

    subcategory_name = models.CharField(max_length=255, unique=True, null=False)
    
    priority = models.IntegerField(null=False)
    class Meta:
        db_table = "SubCategory"
    def __str__(self):
        return f"{self.subcategory_name} (Priority: {self.priority})"


class FurtherSubCategory(models.Model):
    # ForeignKey to Category table
    Subcategory = models.ForeignKey('SubCategory', on_delete=models.CASCADE, related_name='furthersubcategories')

    further_subcategory_name = models.CharField(max_length=255, unique=True, null=False)

    class Meta:
        db_table = "FurtherSubCategory"

    def __str__(self):
        return self.further_subcategory_name
    

class Complaint(models.Model):
    user = models.ForeignKey( AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="complaints")
    subcategory = models.ForeignKey('SubCategory', on_delete=models.CASCADE, related_name='complaints', null=True)
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='complaints', null=True)
    further_subcategory = models.ForeignKey('FurtherSubCategory', on_delete=models.CASCADE, related_name='complaints', null=False)
    description = models.TextField(null=False)
    form_data = models.JSONField(default=dict, null=True, blank=True)
    supporting_file = models.FileField(upload_to='complaints/files/', null=True, blank=True)

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('viewed', 'Viewed'),
        ('resolved', 'Resolved'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    priority = models.IntegerField(null=True, blank=True)  # Stored priority
    expected_resolution_date = models.DateField(null=True, blank=True)  # Changed to DateField
    resolution_date= models.DateField(null=True, blank=True)  # Changed to DateField
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "Complaint"
    def __str__(self):
        return f"Complaint #{self.id} by User {self.user.consumer_no}"
    
