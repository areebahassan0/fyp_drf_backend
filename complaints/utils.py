from datetime import datetime
from django.utils.timezone import now
from .models import Complaint

def status_update():
    # Initialize the priority dictionary
    priority_dict = {
        1: (24, 3),
        2: (48, 9),
        3: (72, 18),
        4: (96, 40),
        5: (120, 65)
    }
    
    # Fetch complaints with status 'pending' or 'viewed'
    complaints = Complaint.objects.filter(status__in=['pending', 'viewed'])
    
    # Get the current date and time
    current_datetime = now()
    current_date = current_datetime.date()  # Only the date part

    # Iterate through each complaint
    for complaint in complaints:
        expected_resolution_date = complaint.expected_resolution_date
        expected_resolution_date = expected_resolution_date
        created_at = complaint.created_at
        priority = complaint.priority

        if not expected_resolution_date:
            continue
        # Check if the expected resolution date is in the past
        if expected_resolution_date < current_date:
            complaint.status = 'resolved'
            complaint.resolution_date = expected_resolution_date
            complaint.save()
            continue  # Move to the next complaint

        # If expected_resolution_date is today or in the future, calculate the difference in hours
        time_diff = current_datetime - created_at
        diff_in_hours = time_diff.total_seconds() // 3600  # Convert seconds to hours

        # Lookup the dictionary for the current priority
        if priority in priority_dict:
            first_value, second_value = priority_dict[priority]

            if diff_in_hours > first_value:
                complaint.status = 'resolved'
                complaint.resolution_date = expected_resolution_date
            elif second_value < diff_in_hours <= first_value:
                complaint.status = 'viewed'
            
            # Save the updated complaint object
            complaint.save()
