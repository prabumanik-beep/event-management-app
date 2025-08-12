from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from scheduling.intelligent_scheduler import solve_meeting_schedule
from scheduling.models import Meeting, Notification

class Command(BaseCommand):
    help = 'Runs the intelligent scheduler to generate and save the optimal meeting schedule.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Runs the scheduler and prints the proposed meetings without saving them to the database.',
        )
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting meeting generation process..."))

        # Run the solver to get the list of proposed meetings
        proposed_meetings = solve_meeting_schedule()

        if not proposed_meetings:
            self.stdout.write(self.style.WARNING("Scheduler did not find any possible meetings. No changes made."))
            return

        if options['dry_run']:
            self.stdout.write(self.style.SUCCESS("--- DRY RUN: Proposed Meetings ---"))
            for i, m in enumerate(proposed_meetings):
                self.stdout.write(
                    f"{i+1}. {m['attendee1'].username} & {m['attendee2'].username} "
                    f"at {m['time_slot']} in {m['room']} (Score: {m['score']:.2f})"
                )
            self.stdout.write(self.style.SUCCESS("--- End of Dry Run ---"))
            return

        try:
            # Use a transaction to ensure this entire block succeeds or fails together.
            with transaction.atomic():
                # --- Improvement: Only delete future meetings ---
                # This preserves historical data for past meetings.
                self.stdout.write("Clearing previously scheduled future meetings...")
                meetings_to_delete = Meeting.objects.filter(time_slot__start_time__gte=timezone.now())
                meetings_to_delete.delete()

                self.stdout.write(f"Creating {len(proposed_meetings)} new meetings...")
                meetings_to_create = [
                    Meeting(**m) for m in proposed_meetings
                ]
                # On PostgreSQL, bulk_create returns the created objects with their new IDs.
                created_meetings = Meeting.objects.bulk_create(meetings_to_create)
                
                self.stdout.write("Creating notifications for new meetings...")
                notifications_to_create = []
                for meeting in created_meetings:
                    # Create a notification for both attendees.
                    notifications_to_create.append(
                        Notification(
                            user=meeting.attendee1,
                            event_type=Notification.EventType.MEETING_SCHEDULED,
                            message=f"New meeting scheduled with {meeting.attendee2.username} at {meeting.time_slot.start_time.strftime('%-I:%M %p')}."
                        )
                    )
                    notifications_to_create.append(
                        Notification(
                            user=meeting.attendee2,
                            event_type=Notification.EventType.MEETING_SCHEDULED,
                            message=f"New meeting scheduled with {meeting.attendee1.username} at {meeting.time_slot.start_time.strftime('%-I:%M %p')}."
                        )
                    )
                Notification.objects.bulk_create(notifications_to_create)
            self.stdout.write(self.style.SUCCESS("Successfully generated and saved new meeting schedule!"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"An error occurred: {e}"))