from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models import Q
from itertools import combinations
from scheduling.models import Meeting, TimeSlot

User = get_user_model()

class Command(BaseCommand):
    help = 'Generates meetings for users with shared interests who do not already have a meeting scheduled.'

    def handle(self, *args, **options):
        self.stdout.write("Starting meeting generation...")

        # Find all users with at least one interest
        users_with_interests = User.objects.filter(profile__interests__isnull=False).distinct().prefetch_related('profile__interests')

        # Get the first available time slot as a placeholder
        try:
            available_time_slot = TimeSlot.objects.first()
            if not available_time_slot:
                self.stdout.write(self.style.ERROR("No available time slots found. Cannot create meetings."))
                return
        except TimeSlot.DoesNotExist:
            self.stdout.write(self.style.ERROR("TimeSlot model not found or no slots exist."))
            return

        # Iterate through all unique pairs of users
        for user1, user2 in combinations(users_with_interests, 2):
            user1_interests = set(user1.profile.interests.all())
            user2_interests = set(user2.profile.interests.all())

            # Check for shared interests
            if user1_interests.intersection(user2_interests):
                # Check if a meeting already exists between these two users
                if not Meeting.objects.filter(Q(attendee1=user1, attendee2=user2) | Q(attendee1=user2, attendee2=user1)).exists():
                    Meeting.objects.create(attendee1=user1, attendee2=user2, time_slot=available_time_slot)
                    self.stdout.write(self.style.SUCCESS(f"Created meeting for {user1.username} and {user2.username}"))
                else:
                    self.stdout.write(self.style.WARNING(f"Meeting already exists for {user1.username} and {user2.username}"))

        self.stdout.write("Meeting generation complete.")