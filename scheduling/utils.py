import collections
from django.db.models import Q
from django.utils import timezone
from .models import Meeting, MeetingFeedback, Notification

def create_notification_if_not_snoozed(user, event_type, message):
    """
    Creates a notification for a user, but only if their notifications
    are not currently snoozed.
    """
    snooze_until = user.profile.notifications_snoozed_until
    if not snooze_until or timezone.now() > snooze_until:
        Notification.objects.create(user=user, event_type=event_type, message=message)

def calculate_average_ratings_for_users(user_ids):
    """
    Efficiently calculates the average rating RECEIVED by a list of users.
    Returns a dictionary mapping user_id to its average rating.
    """
    # Get all meetings involving any of the relevant users
    meetings_qs = Meeting.objects.filter(
        Q(attendee1_id__in=user_ids) | Q(attendee2_id__in=user_ids)
    ).values('id', 'attendee1_id', 'attendee2_id')

    # Get all feedback for those meetings
    feedback_qs = MeetingFeedback.objects.filter(
        meeting_id__in=[m['id'] for m in meetings_qs]
    ).values('reviewer_id', 'rating', 'meeting__attendee1_id', 'meeting__attendee2_id')

    # Process the feedback in Python to calculate average received ratings
    raw_ratings = collections.defaultdict(list)
    for fb in feedback_qs:
        # Determine who was reviewed (the person in the meeting who was not the reviewer)
        reviewed_user_id = fb['meeting__attendee2_id'] if fb['reviewer_id'] == fb['meeting__attendee1_id'] else fb['meeting__attendee1_id']
        if reviewed_user_id in user_ids:
            raw_ratings[reviewed_user_id].append(fb['rating'])

    # Calculate the final average, starting with a default of 3.0 for all users
    avg_ratings = {user_id: 3.0 for user_id in user_ids}
    for user_id, ratings in raw_ratings.items():
        if ratings:
            avg_ratings[user_id] = sum(ratings) / len(ratings)
            
    return avg_ratings