from django.urls import path
from .views import MeetingListView

urlpatterns = [
    # This path is relative to /api/meetings/ as defined in the main urls.py
    path('', MeetingListView.as_view(), name='meeting-list'),
]