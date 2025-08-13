from rest_framework import generics, permissions
from rest_framework.response import Response
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework import status
from .models import Profile, Meeting
# Corrected import statement to only include serializers that exist and are used.
from .serializers import ProfileSerializer, MeetingSerializer
from ics import Calendar, Event

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

class MeetingICSView(APIView):
    """
    Generates and returns an .ics calendar file for a specific meeting.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk, format=None):
        try:
            meeting = Meeting.objects.select_related('time_slot', 'attendee1', 'attendee2').get(pk=pk)
        except Meeting.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # Ensure the user requesting the file is a participant in the meeting
        if request.user != meeting.attendee1 and request.user != meeting.attendee2:
            return Response(status=status.HTTP_403_FORBIDDEN)

        cal = Calendar()
        event = Event()
        event.name = f"Meeting: {meeting.attendee1.username} & {meeting.attendee2.username}"
        event.begin = meeting.time_slot.start_time
        event.end = meeting.time_slot.end_time # Assumes your TimeSlot model has an end_time
        event.description = f"A scheduled meeting between {meeting.attendee1.username} and {meeting.attendee2.username} to discuss shared interests."
        cal.events.add(event)

        response = HttpResponse(cal.serialize(), content_type='text/calendar')
        response['Content-Disposition'] = f'attachment; filename="meeting_{pk}.ics"'
        return response