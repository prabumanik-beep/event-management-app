from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from scheduling.intelligent_scheduler import solve_meeting_schedule
from scheduling.models import Meeting

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
                    Meeting(
                        attendee1=m['attendee1'],
                        attendee2=m['attendee2'],
                        time_slot=m['time_slot'],
                        room=m['room'],
                        score=m['score']
                    ) for m in proposed_meetings
                ]

                # Use bulk_create for high-performance database insertion.
                Meeting.objects.bulk_create(meetings_to_create)

            self.stdout.write(self.style.SUCCESS("Successfully generated and saved new meeting schedule!"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"An error occurred: {e}"))