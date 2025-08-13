from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, Interest, Meeting

class MeetingSerializer(serializers.ModelSerializer):
    """
    Serializer for the Meeting model, including the names of the participants.
    """
    user1 = serializers.StringRelatedField()
    user2 = serializers.StringRelatedField()

    class Meta:
        model = Meeting
        fields = ['id', 'user1', 'user2', 'meeting_time']


class ProfileSerializer(serializers.ModelSerializer):
from rest_framework import generics, permissions
from rest_framework.response import Response
from django.http import JsonResponse
from django.db.models import Q
from .models import Interest, Meeting
from .serializers import ProfileSerializer, MeetingSerializer


class ProfileView(generics.RetrieveUpdateAPIView):
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
        return Meeting.objects.filter(Q(user1=user) | Q(user2=user)).order_by('meeting_time')

def health_check(request):
    return JsonResponse({"status": "ok", "message": "Health check passed"})
from django.urls import path
from .views import ProfileView, MeetingListView

urlpatterns = [
    # The main profile view is handled in the project's urls.py
    # This file is for scheduling-specific URLs if needed in the future.
    path('', MeetingListView.as_view(), name='meeting-list'),
]

