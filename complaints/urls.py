from django.urls import path
from .views import CreateComplaintView, ViewHistory, DeleteComplaintView, UpdateComplaintView, TrackYourComplaint
urlpatterns = [
    path('create/', CreateComplaintView.as_view(), name='create-complaint'),
    path('history/', ViewHistory.as_view(), name='view-history'),
    path('delete/', DeleteComplaintView.as_view(), name='delete-complaint'),
    path('update/', UpdateComplaintView.as_view(), name='update-complaint'),
    path('track/',TrackYourComplaint.as_view(), name='track-complaint'),
    # path('user/',ViewUser.as_view(), name='view-user')
]
