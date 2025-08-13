from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, Meeting, Skill

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['name']

class MeetingSerializer(serializers.ModelSerializer):
    """
    Serializer for the Meeting model, including the names of the participants.
    """
    # These field names now correctly match the Meeting model
    attendee1 = serializers.StringRelatedField()
    attendee2 = serializers.StringRelatedField()
    meeting_time = serializers.DateTimeField(source='time_slot.start_time', read_only=True)

    class Meta:
        model = Meeting
        fields = ['id', 'attendee1', 'attendee2', 'meeting_time', 'score']

class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the user's profile, including their interests.
    """
    username = serializers.CharField(source='user.username', read_only=True)
    interests = SkillSerializer(many=True, read_only=True)
    interest_names = serializers.ListField(
        child=serializers.CharField(max_length=100),
        write_only=True,
        help_text="A list of interest names to set for the profile."
    )

    class Meta:
        model = Profile
        fields = ['username', 'role', 'interests', 'interest_names']

    def update(self, instance, validated_data):
        interest_names = validated_data.pop('interest_names', [])
        instance.interests.clear()
        for name in interest_names:
            skill, _ = Skill.objects.get_or_create(name=name.strip())
            instance.interests.add(skill)
        return super().update(instance, validated_data)
