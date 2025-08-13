from rest_framework import generics, permissions
from rest_framework.response import Response
from django.http import JsonResponse
from django.db.models import Q
from .models import Profile, Meeting
# Corrected import statement to only include serializers that exist and are used.
from .serializers import ProfileSerializer, MeetingSerializer


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    Provides a user's profile and allows them to update their interests.
    """
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Return the profile of the currently authenticated user
        return self.request.user.profile

class MeetingListView(generics.ListAPIView):
    """
    Provides a list of meetings where the currently authenticated user is a participant.
    """
    serializer_class = MeetingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Correctly filter by attendee1/attendee2 and order by the meeting's start time
        return Meeting.objects.filter(Q(attendee1=user) | Q(attendee2=user)).order_by('time_slot__start_time')

def health_check(request):
    """
    A simple health check endpoint for Render to monitor service health.
    """
    return JsonResponse({"status": "ok", "message": "Health check passed"})