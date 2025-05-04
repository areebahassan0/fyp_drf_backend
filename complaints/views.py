from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Complaint, SubCategory, FurtherSubCategory
from .serializers import ComplaintSerializer, ViewHistoryComplaintSerializer, TrackComplaintSerializer
from datetime import timedelta, datetime
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import ValidationError
from .utils import status_update
from fyp.settings import AUTH_USER_MODEL
from user.models import User

class CreateComplaintView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Extract required fields
        # user_id = request.data.get('user_id')
        user = request.user
        if not user.is_active:
            raise ValidationError("User account is inactive. Please contact support.")
        
        further_subcategory_id = request.data.get('further_subcategory_id')
        description = request.data.get('description')
        form_data = request.data.get('form_data')
        supporting_file = request.FILES.get('supporting_file')  # Handle file here

        # Validate and retrieve related objects
        # user = get_object_or_404(AUTH_USER_MODEL, consumer_no=user_id)
        
        further_subcategory = get_object_or_404(FurtherSubCategory, id=further_subcategory_id)
        subcategory = further_subcategory.Subcategory
        category = subcategory.category
        priority = subcategory.priority

        #logic for expected resolution date
        priority_hours_mapping = {
            1: 24,
            2: 48,
            3: 72,
            4: 96,
            5: 120,
        }
        hours_to_add = priority_hours_mapping.get(priority, 1)  # Default to 0 if priority not found
        expected_resolution_date = datetime.now() + timedelta(hours=hours_to_add)

        # Create the complaint
        complaint = Complaint.objects.create(
            user=user,
            further_subcategory=further_subcategory,
            subcategory=subcategory,
            category=category,
            description=description,
            form_data=form_data,
            supporting_file=supporting_file,
            priority=priority,
            expected_resolution_date = expected_resolution_date.date()
        )

        serializer = ComplaintSerializer(complaint)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ViewHistory(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):

        status_update()
        # Extract user_id from request parameters
        # user_id = request.query_params.get('user_id')
        # if not user_id:
        #     return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate and fetch user
        # user = get_object_or_404(AUTH_USER_MODEL, consumer_no=user_id)
        user = request.user
        # Retrieve complaints for the user
        complaints = Complaint.objects.filter(user=user).order_by('-created_at')

        # Serialize the complaints data
        serializer = ViewHistoryComplaintSerializer(complaints, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
    
class DeleteComplaintView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def delete(self, request, *args, **kwargs):

        complaint_id = request.query_params.get('complaint_id')
        complaint = get_object_or_404(Complaint, id=complaint_id)
        complaint.delete()
        return Response({"message": "Complaint deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


class UpdateComplaintView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def patch(self, request, *args, **kwargs):
        # Get complaint_id from the request data
        complaint_id = request.query_params.get('complaint_id')

        if not complaint_id:
            return Response({"error": "Complaint ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve the complaint object
        complaint = get_object_or_404(Complaint, id=complaint_id)

        # Allow updates only to specific fields
        allowed_fields = ['form_data', 'description', 'supporting_file']
        update_data = {key: value for key, value in request.data.items() if key in allowed_fields}

        if not update_data:
            return Response({"error": "No valid fields provided for update."}, status=status.HTTP_400_BAD_REQUEST)

        for field, value in update_data.items():
            setattr(complaint, field, value)
        complaint.save()
        return Response({"message": "Complaint updated successfully."}, status=status.HTTP_200_OK)

class TrackYourComplaint(APIView):

    
    def get(self, request, *args, **kwargs):

        status_update()
        user = request.user
        # user = User.objects.get(consumer_no=user_id)
        # user = get_object_or_404(AUTH_USER_MODEL, consumer_no=user_id)

        unresolved_complaints = Complaint.objects.filter(user=user, status__in=['pending', 'viewed'])

        serialized_complaints = TrackComplaintSerializer(unresolved_complaints, many=True)

        return Response(serialized_complaints.data, status = status.HTTP_200_OK)
    