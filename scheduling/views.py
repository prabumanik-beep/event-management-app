import collections
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db.models import Count, Q, F, Avg, Case, When, Value, IntegerField, CharField
from django.db.models.functions import Concat
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status, generics, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import MeetingFilter, TimeSlotFilter, MyProposalsFilter
from .models import (Meeting, MeetingFeedback, MeetingRescheduleProposal, Notification, Profile, Room, Skill, TimeSlot, UserAvailability)
from .serializers import (AdminUserSerializer, CreateMeetingRescheduleProposalSerializer, EventFeedSerializer, LeaderboardSerializer, MeetingFeedbackSerializer, MeetingRescheduleProposalSerializer, MeetingSerializer, MergeSkillSerializer, MyEventSummarySerializer, MyStatsSerializer, NotificationSerializer, ProfileSerializer, PublicMeetingSerializer, PublicProfileSerializer, RecommendedMatchSerializer, SkillSerializer, TimeSlotSerializer, UserRegistrationSerializer)
from .utils import create_notification_if_not_snoozed, calculate_average_ratings_for_users
from .intelligent_scheduler import calculate_interest_score

User = get_user_model()

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer

class ProfileView(generics.RetrieveUpdateAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.profile

class SkillViewSet(viewsets.ModelViewSet):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name']

    @action(detail=True, methods=['post'], serializer_class=MergeSkillSerializer)
    def merge(self, request, pk=None):
        target_skill = self.get_object()
        serializer = self.get_serializer(data=request.data, context={'target_skill_id': target_skill.id})
        serializer.is_valid(raise_exception=True)
        source_skill = serializer.validated_data['source_skill_id']

        Profile.objects.filter(interests=source_skill).update(interests=target_skill)
        source_skill.delete()
        return Response({'status': 'skills merged successfully'})

class TimeSlotViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TimeSlot.objects.all()
    serializer_class = TimeSlotSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = TimeSlotFilter

    @action(detail=True, methods=['post', 'delete'])
    def set_availability(self, request, pk=None):
        time_slot = self.get_object()
        user = request.user

        if request.method == 'POST':
            _, created = UserAvailability.objects.get_or_create(user=user, time_slot=time_slot)
            status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
            return Response({'status': 'availability set'}, status=status_code)

        elif request.method == 'DELETE':
            UserAvailability.objects.filter(user=user, time_slot=time_slot).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

class MeetingViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MeetingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = MeetingFilter
    ordering_fields = ['time_slot__start_time', 'score']

    def get_queryset(self):
        user = self.request.user
        return Meeting.objects.filter(Q(attendee1=user) | Q(attendee2=user)).select_related('time_slot', 'room', 'attendee1', 'attendee2')

    @action(detail=True, methods=['post'], serializer_class=CreateMeetingRescheduleProposalSerializer)
    def propose_reschedule(self, request, pk=None):
        meeting = self.get_object()
        # Pass meeting to context for validation.
        serializer = self.get_serializer(data=request.data, context={'meeting': meeting, 'request': request})
        serializer.is_valid(raise_exception=True)
        # Add the meeting and proposer during the save operation.
        proposal = serializer.save(meeting=meeting, proposer=request.user)

        # Serialize the created proposal instance to return the full object.
        response_serializer = MeetingRescheduleProposalSerializer(proposal, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        meeting = self.get_object()
        other_attendee = meeting.attendee1 if meeting.attendee2 == request.user else meeting.attendee2
        
        create_notification_if_not_snoozed(
            other_attendee,
            Notification.EventType.MEETING_CANCELLED,
            f"Your meeting with {request.user.username} at {meeting.time_slot} has been cancelled."
        )
        
        meeting.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class MyProposalsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MeetingRescheduleProposalSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = MyProposalsFilter

    def get_queryset(self):
        user = self.request.user
        return MeetingRescheduleProposal.objects.filter(
            Q(proposer=user) | Q(meeting__attendee1=user) | Q(meeting__attendee2=user)
        ).exclude(
            proposer=user, status__in=[MeetingRescheduleProposal.Status.ACCEPTED, MeetingRescheduleProposal.Status.REJECTED]
        ).select_related('meeting__time_slot', 'proposer', 'proposed_time_slot').distinct()

class RespondToProposalViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return MeetingRescheduleProposal.objects.filter(
            Q(meeting__attendee1=user) | Q(meeting__attendee2=user)
        ).exclude(proposer=user)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        proposal = self.get_object()
        meeting = proposal.meeting
        meeting.time_slot = proposal.proposed_time_slot
        meeting.save()
        proposal.status = MeetingRescheduleProposal.Status.ACCEPTED
        proposal.save()
        
        create_notification_if_not_snoozed(
            proposal.proposer,
            Notification.EventType.PROPOSAL_ACCEPTED,
            f"Your proposal to reschedule with {request.user.username} was accepted."
        )
        
        return Response({'status': 'Proposal accepted and meeting rescheduled.'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        proposal = self.get_object()
        proposal.status = MeetingRescheduleProposal.Status.REJECTED
        proposal.save()

        create_notification_if_not_snoozed(
            proposal.proposer,
            Notification.EventType.PROPOSAL_REJECTED,
            f"Your proposal to reschedule with {request.user.username} was rejected."
        )

        return Response({'status': 'Proposal rejected.'})

class WhatsOnNowViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PublicMeetingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        now = timezone.now()
        return Meeting.objects.filter(time_slot__start_time__lte=now, time_slot__end_time__gte=now)

class PublicProfileViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PublicProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Profile.objects.filter(checked_in=True).select_related('user')

    @action(detail=True, methods=['post'])
    def request_meeting(self, request, pk=None):
        target_profile = self.get_object()
        if target_profile.user == request.user:
            return Response({'error': 'You cannot request a meeting with yourself.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if request.user.profile.blocked_users.filter(pk=target_profile.pk).exists():
            return Response({'error': 'Cannot request meeting with a user you have blocked.'}, status=status.HTTP_403_FORBIDDEN)

        send_mail(
            f"Meeting Request from {request.user.username}",
            f"{request.user.username} would like to schedule a meeting with you at the event.",
            'noreply@vibecoding.com',
            [target_profile.user.email]
        )
        return Response({'status': 'Meeting request sent.'})

    @action(detail=True, methods=['post'])
    def block(self, request, pk=None):
        target_profile = self.get_object()
        request.user.profile.blocked_users.add(target_profile)
        return Response({'status': 'User blocked.'})

    @action(detail=True, methods=['post'])
    def unblock(self, request, pk=None):
        target_profile = self.get_object()
        request.user.profile.blocked_users.remove(target_profile)
        return Response({'status': 'User unblocked.'})

class UserAdminViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminUser]

    @action(detail=True, methods=['post'])
    def check_in(self, request, pk=None):
        user = self.get_object()
        user.profile.checked_in = True
        user.profile.save()
        return Response({'status': f'{user.username} checked in.'})

class LeaderboardViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LeaderboardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.annotate(
            meeting_count=Count('meetings_as_attendee1') + Count('meetings_as_attendee2')
        ).filter(meeting_count__gt=0).order_by('-meeting_count', 'username')

class MyStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        user_meeting_count = Meeting.objects.filter(Q(attendee1=user) | Q(attendee2=user)).count()

        rank = None
        if user_meeting_count > 0:
            # More performant way to calculate rank without loading the whole leaderboard.
            # 1. Count users with more meetings.
            higher_rank_count = User.objects.annotate(
                m_count=Count('meetings_as_attendee1') + Count('meetings_as_attendee2')
            ).filter(m_count__gt=user_meeting_count).count()

            # 2. Count users with the same number of meetings but an earlier username for tie-breaking.
            same_rank_tie_break_count = User.objects.annotate(
                m_count=Count('meetings_as_attendee1') + Count('meetings_as_attendee2')
            ).filter(
                m_count=user_meeting_count,
                username__lt=user.username
            ).count()

            rank = higher_rank_count + same_rank_tie_break_count + 1

        serializer = MyStatsSerializer(data={'username': user.username, 'meeting_count': user_meeting_count, 'rank': rank,})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)

class RecommendedMatchesView(generics.ListAPIView):
    serializer_class = RecommendedMatchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        existing_partners = User.objects.filter(
            Q(meetings_as_attendee1__attendee2=user) | Q(meetings_as_attendee2__attendee1=user)
        ).values_list('id', flat=True)

        potential_matches_profiles = list(Profile.objects.filter(checked_in=True).exclude(user=user).exclude(user_id__in=existing_partners).select_related('user').prefetch_related('interests'))

        # Use the new utility function
        all_relevant_user_ids = [p.user_id for p in potential_matches_profiles] + [user.id]
        avg_ratings = calculate_average_ratings_for_users(all_relevant_user_ids)

        user_data = {
            'interests': set(user.profile.interests.values_list('id', flat=True)),
            'role': user.profile.role,
            'avg_rating_received': avg_ratings.get(user.id, 3.0) # Default to 3.0 if user has no ratings
        }

        scored_matches = []
        for profile in potential_matches_profiles:
            match_data = {
                'interests': set(profile.interests.values_list('id', flat=True)),
                'role': profile.role,
                'avg_rating_received': avg_ratings.get(profile.user_id, 3.0) # Default to 3.0 if match has no ratings
            }
            score = calculate_interest_score(user_data, match_data)
            if score > 0:
                scored_matches.append({'user': profile, 'match_score': score})

        return sorted(scored_matches, key=lambda x: x['match_score'], reverse=True)

class MyEventFeedView(generics.ListAPIView):
    serializer_class = EventFeedSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Get meetings and annotate them to match the feed structure
        meetings = Meeting.objects.filter(
            Q(attendee1=user) | Q(attendee2=user)
        ).annotate(
            event_type=Value('MEETING_SCHEDULED', output_field=CharField()),
            timestamp=F('time_slot__start_time'),
            details=Concat(
                Value('Meeting with '),
                Case(
                    When(attendee1=user, then=F('attendee2__username')),
                    default=F('attendee1__username')
                ),
                output_field=CharField()
            )
        ).values('event_type', 'timestamp', 'details')

        # Get proposals and annotate them
        proposals = MeetingRescheduleProposal.objects.filter(
            proposer=user
        ).annotate(
            event_type=Value('PROPOSAL_SENT', output_field=CharField()),
            timestamp=F('created_at'),
            details=Value('Proposal sent for meeting', output_field=CharField())
        ).values('event_type', 'timestamp', 'details')

        # Combine them in the database and order by timestamp
        return meetings.union(proposals).order_by('-timestamp')

class MyEventSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        total_meetings = Meeting.objects.filter(Q(attendee1=user) | Q(attendee2=user)).count()
        pending_proposals_count = MeetingRescheduleProposal.objects.filter(
            (Q(meeting__attendee1=user) | Q(meeting__attendee2=user)) & Q(status=MeetingRescheduleProposal.Status.PENDING)
        ).exclude(proposer=user).count()
        top_interests = list(user.profile.interests.values_list('name', flat=True))

        serializer = MyEventSummarySerializer(data={'total_meetings': total_meetings, 'pending_proposals_count': pending_proposals_count, 'top_interests': top_interests,})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)

class MeetingFeedbackViewSet(viewsets.ModelViewSet):
    serializer_class = MeetingFeedbackSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MeetingFeedback.objects.filter(meeting_id=self.kwargs['pk'])

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['meeting'] = get_object_or_404(Meeting, pk=self.kwargs['pk'])
        return context

    def perform_create(self, serializer):
        meeting = get_object_or_404(Meeting, pk=self.kwargs['pk'])
        serializer.save(reviewer=self.request.user, meeting=meeting)

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.notifications.all()

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        self.get_queryset().update(is_read=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

class SnoozeNotificationsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        duration_hours = request.data.get('duration_hours', 24)
        snooze_until = timezone.now() + timezone.timedelta(hours=int(duration_hours))
        request.user.profile.notifications_snoozed_until = snooze_until
        request.user.profile.save()
        return Response({'status': f'Notifications snoozed until {snooze_until}'})

class UnSnoozeNotificationsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.profile.notifications_snoozed_until = None
        request.user.profile.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ClearInterestsView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        request.user.profile.interests.clear()
        return Response(status=status.HTTP_204_NO_CONTENT)