import django_filters
from django.db.models import Q
from django.utils import timezone
from .models import Meeting, MeetingRescheduleProposal, TimeSlot


class MeetingFilter(django_filters.FilterSet):
    is_future = django_filters.BooleanFilter(
        method='filter_is_future'
    )

    class Meta:
        model = Meeting
        fields = ['is_future']

    def filter_is_future(self, queryset, name, value):
        if value:
            return queryset.filter(time_slot__start_time__gte=timezone.now())
        return queryset


class TimeSlotFilter(django_filters.FilterSet):
    has_available_rooms = django_filters.BooleanFilter(
        method='filter_has_available_rooms'
    )
    is_user_available = django_filters.BooleanFilter(
        method='filter_is_user_available'
    )

    class Meta:
        model = TimeSlot
        fields = ['has_available_rooms', 'is_user_available']

    def filter_has_available_rooms(self, queryset, name, value):
        return queryset.annotate(num_meetings=Q(meetings__isnull=False)).filter(num_meetings__lt=1)

    def filter_is_user_available(self, queryset, name, value):
        return queryset.filter(available_users=self.request.user)


class MyProposalsFilter(django_filters.FilterSet):
    class Meta:
        model = MeetingRescheduleProposal
        fields = ['status']