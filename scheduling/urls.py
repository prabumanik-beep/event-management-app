from django.urls import path
from .views import MeetingListView, MeetingICSView

urlpatterns = [
    # This path is relative to /api/meetings/ as defined in the main urls.py
    path('', MeetingListView.as_view(), name='meeting-list'),
    path('<int:pk>/ical/', MeetingICSView.as_view(), name='meeting-ical'),
]