from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

class Skill(models.Model):
    """Represents a skill or interest, like 'Python' or 'React'."""
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Profile(models.Model):
    """Extends the default User model with event-specific information."""
    class Role(models.TextChoices):
        ATTENDEE = 'ATT', 'Attendee'
        MENTOR = 'MEN', 'Mentor'
        MENTEE = 'MNE', 'Mentee'

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    interests = models.ManyToManyField(Skill, blank=True, related_name='profiles')
    role = models.CharField(max_length=3, choices=Role.choices, default=Role.ATTENDEE)
    checked_in = models.BooleanField(default=False)
    notifications_snoozed_until = models.DateTimeField(null=True, blank=True)
    blocked_users = models.ManyToManyField(
        'self', symmetrical=False, blank=True, related_name='blocked_by'
    )

    def __str__(self):
        return self.user.username

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Create a profile for a new user, or just save the existing one."""
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()

class TimeSlot(models.Model):
    """Represents a block of time during the event."""
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    description = models.CharField(max_length=255, blank=True)
    available_users = models.ManyToManyField(
        User, through='UserAvailability', related_name='available_slots'
    )

    def __str__(self):
        return f"{self.start_time.strftime('%Y-%m-%d %H:%M')} - {self.end_time.strftime('%H:%M')}"

class UserAvailability(models.Model):
    """A through model linking Users to the TimeSlots they are available for."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'time_slot')
        verbose_name_plural = "User Availabilities"

class Room(models.Model):
    """Represents a physical or virtual room for meetings."""
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Meeting(models.Model):
    """Represents a scheduled meeting between two users."""
    attendee1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meetings_as_attendee1')
    attendee2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meetings_as_attendee2')
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, related_name='meetings')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='meetings')
    score = models.FloatField(default=0.0, help_text="Interest score for this match")

    class Meta:
        unique_together = ('time_slot', 'room') # A room can only have one meeting at a time

class MeetingRescheduleProposal(models.Model):
    """Represents a proposal to reschedule a meeting."""
    class Status(models.TextChoices):
        PENDING = 'PEND', 'Pending'
        ACCEPTED = 'ACPT', 'Accepted'
        REJECTED = 'REJ', 'Rejected'

    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='proposals')
    proposer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_proposals')
    proposed_time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    status = models.CharField(max_length=4, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

class MeetingFeedback(models.Model):
    """Represents feedback submitted by an attendee for a meeting."""
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='feedback')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_feedback')
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('meeting', 'reviewer')

class Notification(models.Model):
    """Represents a notification for a user."""
    class EventType(models.TextChoices):
        MEETING_CANCELLED = 'MTG_CNL', 'Meeting Cancelled'
        PROPOSAL_RECEIVED = 'PRP_RCV', 'Proposal Received'
        PROPOSAL_ACCEPTED = 'PRP_ACC', 'Proposal Accepted'
        PROPOSAL_REJECTED = 'PRP_REJ', 'Proposal Rejected'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    event_type = models.CharField(max_length=7, choices=EventType.choices)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']