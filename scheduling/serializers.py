from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import (Meeting, MeetingFeedback, MeetingRescheduleProposal, Notification, Profile, Skill, TimeSlot, UserAvailability)

User = get_user_model()

class SkillSerializer(serializers.ModelSerializer):
    """Serializer for the Skill model."""
    class Meta:
        model = Skill
        fields = ['id', 'name']

class MergeSkillSerializer(serializers.Serializer):
    """Serializer for validating the skill merge action payload."""
    source_skill_id = serializers.PrimaryKeyRelatedField(
        queryset=Skill.objects.all(),
        help_text="The ID of the skill to merge from and then delete."
    )

    def validate(self, data):
        if self.context.get('target_skill_id') == data['source_skill_id'].id:
            raise serializers.ValidationError("Cannot merge a skill with itself.")
        return data

class PublicProfileSerializer(serializers.ModelSerializer):
    """Serializer for publicly listing attendee profiles."""
    username = serializers.CharField(source='user.username', read_only=True)
    interests = SkillSerializer(many=True, read_only=True)
    role = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = Profile
        fields = ['id', 'username', 'role', 'interests']

class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for the user's own profile, allowing interest updates."""
    username = serializers.CharField(source='user.username', read_only=True)
    interests = SkillSerializer(many=True, read_only=True)
    blocked_users = PublicProfileSerializer(many=True, read_only=True)
    # This new field allows the frontend to send a list of strings.
    interest_names = serializers.ListField(
        child=serializers.CharField(max_length=100),
        write_only=True,
        help_text="A list of skill names to set as the user's interests."
    )
    role = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = Profile
        fields = ['id', 'username', 'interests', 'interest_names', 'role', 'blocked_users']

    def update(self, instance, validated_data):
        # Custom update logic to handle creating/assigning skills by name.
        interest_names = validated_data.pop('interest_names', None)
        if interest_names is not None:
            skills = []
            for name in interest_names:
                # Use get_or_create for robust, case-insensitive skill handling.
                skill, _ = Skill.objects.get_or_create(name__iexact=name, defaults={'name': name.strip()})
                skills.append(skill)
            instance.interests.set(skills)
        return super().update(instance, validated_data)

class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for creating a new user account."""
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'first_name', 'last_name')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data.get('email', ''),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user

class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer for admin-facing user management, including check-in status."""
    checked_in = serializers.BooleanField(source='profile.checked_in', read_only=True)
    role = serializers.CharField(source='profile.get_role_display', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'checked_in', 'role']

class LeaderboardSerializer(serializers.ModelSerializer):
    """Serializer for the meeting leaderboard."""
    meeting_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'meeting_count']

class MyStatsSerializer(serializers.Serializer):
    """Serializer for the user's personal stats and rank."""
    username = serializers.CharField(read_only=True)
    meeting_count = serializers.IntegerField(read_only=True)
    rank = serializers.IntegerField(read_only=True, allow_null=True)

class RecommendedMatchSerializer(serializers.Serializer):
    """Serializer for a recommended user match."""
    user = PublicProfileSerializer(read_only=True)
    match_score = serializers.IntegerField(read_only=True)

class EventFeedSerializer(serializers.Serializer):
    """Serializer for a single event in a user's activity feed."""
    event_type = serializers.CharField(read_only=True)
    timestamp = serializers.DateTimeField(read_only=True)
    details = serializers.CharField(read_only=True)

class MyEventSummarySerializer(serializers.Serializer):
    """Serializer for the user's personal event summary."""
    total_meetings = serializers.IntegerField(read_only=True)
    pending_proposals_count = serializers.IntegerField(read_only=True)
    top_interests = serializers.ListField(child=serializers.CharField(), read_only=True)

class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for user notifications."""
    class Meta:
        model = Notification
        fields = ['id', 'event_type', 'message', 'is_read', 'created_at']

class SimpleUserSerializer(serializers.ModelSerializer):
    """A simple serializer to represent a user in a meeting context."""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']

class MeetingFeedbackSerializer(serializers.ModelSerializer):
    """Serializer for creating and viewing meeting feedback."""
    reviewer = SimpleUserSerializer(read_only=True)

    class Meta:
        model = MeetingFeedback
        fields = ['id', 'reviewer', 'rating', 'comments', 'created_at']
        read_only_fields = ['id', 'reviewer', 'created_at']

    def validate(self, data):
        meeting = self.context['meeting']
        reviewer = self.context['request'].user

        if reviewer not in [meeting.attendee1, meeting.attendee2]:
            raise serializers.ValidationError("You can only provide feedback for meetings you attended.")

        if MeetingFeedback.objects.filter(meeting=meeting, reviewer=reviewer).exists():
            raise serializers.ValidationError("You have already submitted feedback for this meeting.")

        return data

class TimeSlotSerializer(serializers.ModelSerializer):
    """Serializer for TimeSlot model, with added context for the current user."""
    is_current_user_available = serializers.SerializerMethodField()

    class Meta:
        model = TimeSlot
        fields = [
            'id', 'start_time', 'end_time', 'description',
            'is_current_user_available'
        ]

    def get_is_current_user_available(self, obj: TimeSlot) -> bool:
        """Check if the user making the request is available for this slot."""
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        # This is an efficient check that hits the database only once.
        return obj.available_users.filter(pk=user.pk).exists()

class BaseMeetingSerializer(serializers.ModelSerializer):
    """Base serializer for meeting details."""
    time_slot = TimeSlotSerializer(read_only=True)
    room = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Meeting
        fields = ['id', 'time_slot', 'room', 'score']

class MeetingSerializer(BaseMeetingSerializer):
    """Serializer for a user's personal meeting schedule."""
    other_attendee = serializers.SerializerMethodField()

    class Meta(BaseMeetingSerializer.Meta):
        fields = BaseMeetingSerializer.Meta.fields + ['other_attendee']

    def get_other_attendee(self, obj: Meeting):
        """Return the user who is NOT the one making the request."""
        current_user = self.context['request'].user
        other_user = obj.attendee2 if obj.attendee1 == current_user else obj.attendee1
        return SimpleUserSerializer(other_user).data

class PublicMeetingSerializer(BaseMeetingSerializer):
    """Serializer for publicly listing meetings, e.g., for 'What's On Now'."""
    attendee1 = SimpleUserSerializer(read_only=True)
    attendee2 = SimpleUserSerializer(read_only=True)

    class Meta(BaseMeetingSerializer.Meta):
        fields = BaseMeetingSerializer.Meta.fields + ['attendee1', 'attendee2']

class MeetingRescheduleProposalSerializer(serializers.ModelSerializer):
    """Serializer for viewing meeting reschedule proposals."""
    meeting = MeetingSerializer(read_only=True)
    proposer = SimpleUserSerializer(read_only=True)
    proposed_time_slot = TimeSlotSerializer(read_only=True)
    direction = serializers.SerializerMethodField()

    class Meta:
        model = MeetingRescheduleProposal
        fields = ['id', 'meeting', 'proposer', 'proposed_time_slot', 'status', 'created_at', 'direction']

    def get_direction(self, obj: MeetingRescheduleProposal) -> str:
        """Indicates if the proposal was sent or received by the current user."""
        user = self.context['request'].user
        if obj.proposer == user:
            return 'sent'
        return 'received'
class CreateMeetingRescheduleProposalSerializer(serializers.ModelSerializer):
    """Serializer for creating a new MeetingRescheduleProposal."""
    # Renaming to match the model field is more conventional.
    # The client will send a payload like: {"proposed_time_slot": <id>}
    proposed_time_slot = serializers.PrimaryKeyRelatedField(
        queryset=TimeSlot.objects.all(),
        write_only=True
    )

    class Meta:
        model = MeetingRescheduleProposal
        fields = ['proposed_time_slot']
    
    def validate_proposed_time_slot(self, value):
        """Check that the proposed time slot is not the same as the current one."""
        meeting = self.context.get('meeting')
        if not meeting:
            raise serializers.ValidationError("Meeting context is required for validation.")
        if value == meeting.time_slot:
            raise serializers.ValidationError("Cannot propose the same time slot.")
        # You could add more validation here, e.g., ensure the other user is available.
        return value
    # The custom `create` method is removed. The view will now call
    # `serializer.save(meeting=..., proposer=...)` and the default
    # ModelSerializer.create will handle creating the instance.