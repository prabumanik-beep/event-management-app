from django.contrib import admin
from .models import (Meeting, MeetingFeedback, MeetingRescheduleProposal, Profile, Room, Skill, TimeSlot, UserAvailability)


class UserAvailabilityInline(admin.TabularInline):
    """
    Makes UserAvailability editable directly from the TimeSlot admin page.
    This provides a clear view of which users are available for a slot.
    """
    model = UserAvailability
    extra = 1  # Shows one extra empty row for adding new availabilities.
    raw_id_fields = ('user',)  # Uses a search popup for users, which is better for performance.
    verbose_name = "Available User"
    verbose_name_plural = "Available Users"


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    """Admin view for TimeSlot."""
    list_display = ('__str__', 'start_time', 'end_time', 'available_user_count')
    list_filter = ('start_time',)
    inlines = [UserAvailabilityInline]

    def get_queryset(self, request):
        # Prefetch related users to optimize the count query in the list display.
        return super().get_queryset(request).prefetch_related('available_users')

    def available_user_count(self, obj):
        # This uses the prefetched data, so it's efficient.
        return obj.available_users.count()
    
    available_user_count.short_description = 'Available Users Count'


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    """Admin view for generated Meetings."""
    list_display = ('time_slot', 'room', 'attendee1', 'attendee2', 'score')
    list_filter = ('time_slot', 'room')
    search_fields = ('attendee1__username', 'attendee2__username')
    raw_id_fields = ('attendee1', 'attendee2', 'time_slot', 'room')
    ordering = ('time_slot__start_time', 'room__name')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Admin view for user Profiles."""
    list_display = ('user', 'get_user_email', 'role')
    list_filter = ('role',)
    search_fields = ('user__username',)
    raw_id_fields = ('user',)
    filter_horizontal = ('interests',)

    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'Email'


@admin.register(MeetingRescheduleProposal)
class MeetingRescheduleProposalAdmin(admin.ModelAdmin):
    """Admin view for MeetingRescheduleProposal."""
    list_display = ('__str__', 'proposer', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    raw_id_fields = ('meeting', 'proposer', 'proposed_time_slot')

@admin.register(MeetingFeedback)
class MeetingFeedbackAdmin(admin.ModelAdmin):
    """Admin view for MeetingFeedback."""
    list_display = ('meeting', 'reviewer', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('meeting__attendee1__username', 'meeting__attendee2__username', 'reviewer__username', 'comments')
    raw_id_fields = ('meeting', 'reviewer')

admin.site.register(Skill)
admin.site.register(Room)