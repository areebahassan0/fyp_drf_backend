from rest_framework import serializers
from .models import Complaint, User

class ComplaintSerializer(serializers.ModelSerializer):

    expected_resolution_date = serializers.DateField()
    resolution_date = serializers.DateField()

    class Meta:
        model = Complaint
        fields = '__all__'

class ViewHistoryComplaintSerializer(serializers.ModelSerializer):
    further_subcategory_name = serializers.CharField(source='further_subcategory.further_subcategory_name', read_only=True)

    class Meta:
        model = Complaint
        fields = [
            'id',
            'status',
            'expected_resolution_date',
            'created_at',
            'resolution_date',
            'form_data',
            'description',
            'supporting_file',
            'further_subcategory_name',
        ]

class TrackComplaintSerializer(serializers.ModelSerializer):
    further_subcategory_name = serializers.CharField(source='further_subcategory.further_subcategory_name', read_only=True)

    class Meta:
        model = Complaint
        fields = [
            'id',
            'status',
            'expected_resolution_date',
            'created_at',
            'form_data',
            'description',
            'supporting_file',
            'further_subcategory_name',
        ]
# class UserSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = User
#         fields = '__all__'
