import pytest
from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from ..models import (Meeting, MeetingFeedback, MeetingRescheduleProposal, Notification, Profile, Room, Skill, TimeSlot, UserAvailability)

User = get_user_model()

# Marks all tests in this file as needing database access
pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    """A fixture to provide an API client instance."""
    return APIClient()


@pytest.fixture
def test_user():
    """A fixture to create a standard user."""
    return User.objects.create_user(username='testuser', password='password123', email='testuser@example.com')

@pytest.fixture
def other_user():
    """A fixture to create a second user for testing permissions."""
    return User.objects.create_user(username='otheruser', password='password123', email='otheruser@example.com')

@pytest.fixture
def admin_user():
    """A fixture to create a user with admin privileges."""
    return User.objects.create_superuser(username='adminuser', password='password123', email='admin@example.com')

@pytest.fixture
def time_slot():
    """A fixture to create a sample TimeSlot."""
    now = timezone.now()
    return TimeSlot.objects.create(
        start_time=now,
        end_time=now + timezone.timedelta(hours=1),
        description="Networking Block"
    )

@pytest.fixture
def room():
    """A fixture to create a sample Room."""
    return Room.objects.create(name="Conference Room A")

@pytest.fixture
def skills():
    """A fixture to create a few sample Skill objects."""
    skill1 = Skill.objects.create(name='Python')
    skill2 = Skill.objects.create(name='Django')
    skill3 = Skill.objects.create(name='React')
    return [skill1, skill2, skill3]


def test_set_availability_post_success(api_client, test_user, time_slot):
    """
    GIVEN an authenticated user and a time slot
    WHEN the user POSTs to the set_availability endpoint
    THEN they should be marked as available and receive a 201 CREATED status.
    """
    api_client.force_authenticate(user=test_user)
    url = reverse('timeslot-set-availability', kwargs={'pk': time_slot.pk})
    
    response = api_client.post(url)
    
    assert response.status_code == 201
    assert UserAvailability.objects.filter(user=test_user, time_slot=time_slot).exists()


def test_set_availability_post_idempotent(api_client, test_user, time_slot):
    """
    GIVEN a user is already marked as available
    WHEN they POST to the set_availability endpoint again
    THEN the request should succeed with a 200 OK status and not create a duplicate entry.
    """
    UserAvailability.objects.create(user=test_user, time_slot=time_slot)
    api_client.force_authenticate(user=test_user)
    url = reverse('timeslot-set-availability', kwargs={'pk': time_slot.pk})
    
    response = api_client.post(url)
    
    assert response.status_code == 200
    assert UserAvailability.objects.filter(user=test_user, time_slot=time_slot).count() == 1


def test_set_availability_delete_success(api_client, test_user, time_slot):
    """
    GIVEN a user is marked as available
    WHEN they send a DELETE request to the set_availability endpoint
    THEN their availability should be removed and they receive a 204 NO CONTENT status.
    """
    UserAvailability.objects.create(user=test_user, time_slot=time_slot)
    api_client.force_authenticate(user=test_user)
    url = reverse('timeslot-set-availability', kwargs={'pk': time_slot.pk})
    
    response = api_client.delete(url)
    
    assert response.status_code == 204
    assert not UserAvailability.objects.filter(user=test_user, time_slot=time_slot).exists()


def test_set_availability_unauthenticated(api_client, time_slot):
    """
    GIVEN an unauthenticated user
    WHEN they attempt to POST to the set_availability endpoint
    THEN they should receive a 401 UNAUTHORIZED error.
    """
    url = reverse('timeslot-set-availability', kwargs={'pk': time_slot.pk})
    response = api_client.post(url)
    assert response.status_code == 401


def test_get_profile_success(api_client, test_user):
    """
    GIVEN an authenticated user
    WHEN they make a GET request to the profile endpoint
    THEN they should receive their profile data with a 200 OK status.
    """
    api_client.force_authenticate(user=test_user)
    url = reverse('user-profile')
    
    response = api_client.get(url)
    
    assert response.status_code == 200
    assert response.data['username'] == test_user.username
    assert 'interests' in response.data


def test_update_profile_interests_success(api_client, test_user, skills):
    """
    GIVEN an authenticated user and some skills
    WHEN they make a PUT request to the profile endpoint with new interest IDs
    THEN their profile should be updated and they receive a 200 OK status.
    """
    api_client.force_authenticate(user=test_user)
    url = reverse('user-profile')
    
    # User initially has no interests
    assert test_user.profile.interests.count() == 0

    # We want to add the first two skills as interests
    skill_ids_to_add = [skills[0].id, skills[1].id]
    payload = {'interest_ids': skill_ids_to_add}
    
    response = api_client.put(url, data=payload)
    
    assert response.status_code == 200
    assert len(response.data['interests']) == 2
    
    # Verify the change in the database
    test_user.profile.refresh_from_db()
    assert test_user.profile.interests.count() == 2
    assert test_user.profile.interests.filter(name='Python').exists()
    assert test_user.profile.interests.filter(name='Django').exists()
    assert not test_user.profile.interests.filter(name='React').exists()


def test_get_meetings_returns_only_own_meetings(api_client, test_user, other_user, time_slot, room):
    """
    GIVEN several meetings exist in the database
    WHEN an authenticated user requests their meetings
    THEN they should only receive a list of meetings they are an attendee of.
    """
    # Create a third user for the meeting we shouldn't see
    third_user = User.objects.create_user(username='thirduser', password='password123')

    # Meeting 1: test_user is attendee1
    meeting1 = Meeting.objects.create(
        attendee1=test_user, attendee2=other_user, time_slot=time_slot, room=room
    )

    # Create a second time slot to avoid unrealistic double-booking in the test
    other_time_slot = TimeSlot.objects.create(
        start_time=timezone.now() + timezone.timedelta(hours=2),
        end_time=timezone.now() + timezone.timedelta(hours=3)
    )
    # Meeting 2: test_user is attendee2
    meeting2 = Meeting.objects.create(
        attendee1=other_user, attendee2=test_user, time_slot=other_time_slot, room=room
    )

    # Meeting 3: A meeting test_user is NOT a part of
    meeting_to_exclude = Meeting.objects.create(
        attendee1=other_user, attendee2=third_user, time_slot=time_slot, room=Room.objects.create(name="Room B")
    )

    api_client.force_authenticate(user=test_user)
    url = reverse('meeting-list')
    response = api_client.get(url)

    assert response.status_code == 200
    assert response.data['count'] == 2
    response_meeting_ids = {meeting['id'] for meeting in response.data['results']}
    assert {meeting1.id, meeting2.id} == response_meeting_ids


def test_admin_can_create_skill(api_client, admin_user):
    """
    GIVEN an authenticated admin user
    WHEN they POST to the skills endpoint
    THEN a new skill should be created and they receive a 201 CREATED status.
    """
    api_client.force_authenticate(user=admin_user)
    url = reverse('skill-list')
    payload = {'name': 'Kubernetes'}

    response = api_client.post(url, data=payload)

    assert response.status_code == 201
    assert Skill.objects.filter(name='Kubernetes').exists()


def test_non_admin_cannot_create_skill(api_client, test_user):
    """
    GIVEN an authenticated non-admin user
    WHEN they POST to the skills endpoint
    THEN they should be denied with a 403 FORBIDDEN status.
    """
    api_client.force_authenticate(user=test_user)
    url = reverse('skill-list')
    payload = {'name': 'ForbiddenSkill'}

    response = api_client.post(url, data=payload)

    assert response.status_code == 403
    assert not Skill.objects.filter(name='ForbiddenSkill').exists()


def test_skill_search_filter_works(api_client, admin_user, skills):
    """
    GIVEN an admin user and several skills
    WHEN they make a GET request to the skills endpoint with a search query
    THEN they should receive a list containing only the matching skills.
    """
    # The `skills` fixture creates 'Python', 'Django', 'React'
    api_client.force_authenticate(user=admin_user)
    url = reverse('skill-list')
    
    # Search for skills containing 'py' (case-insensitive)
    response = api_client.get(url, {'search': 'py'})

    assert response.status_code == 200
    results = response.data['results'] if 'results' in response.data else response.data
    
    assert len(results) == 1
    assert results[0]['name'] == 'Python'
    assert 'Django' not in [skill['name'] for skill in results]


def test_skill_ordering_filter_works(api_client, admin_user, skills):
    """
    GIVEN an admin user and several skills
    WHEN they make a GET request to the skills endpoint with a descending ordering query
    THEN they should receive a list of skills sorted in descending order by name.
    """
    # The `skills` fixture creates 'Python', 'Django', 'React'
    api_client.force_authenticate(user=admin_user)
    url = reverse('skill-list')

    # Request descending order by name
    response = api_client.get(url, {'ordering': '-name'})

    assert response.status_code == 200
    results = response.data['results'] if 'results' in response.data else response.data

    # Expected order: React, Python, Django
    assert len(results) == 3
    skill_names = [skill['name'] for skill in results]
    assert skill_names == ['React', 'Python', 'Django']


def test_meeting_viewset_is_paginated(api_client, test_user, other_user, room):
    """
    GIVEN more meetings than the page size exist for a user
    WHEN they make a GET request to the meetings endpoint
    THEN the response should be paginated correctly.
    """
    # Create 30 meetings for the test_user
    for i in range(30):
        ts = TimeSlot.objects.create(
            start_time=timezone.now() + timezone.timedelta(hours=i),
            end_time=timezone.now() + timezone.timedelta(hours=i + 1)
        )
        Meeting.objects.create(attendee1=test_user, attendee2=other_user, time_slot=ts, room=room)

    api_client.force_authenticate(user=test_user)
    url = reverse('meeting-list')
    response = api_client.get(url)

    assert response.status_code == 200
    # Check for pagination keys
    assert 'count' in response.data
    assert 'next' in response.data
    assert 'previous' in response.data
    assert 'results' in response.data

    assert response.data['count'] == 30
    assert len(response.data['results']) == 25  # Default page_size from StandardResultsSetPagination
    assert response.data['next'] is not None
    assert response.data['previous'] is None


def test_meeting_ordering_by_score_works(api_client, test_user, other_user, room):
    """
    GIVEN a user with several meetings with different scores
    WHEN they make a GET request to the meetings endpoint ordering by score descending
    THEN they should receive a list of meetings sorted by score.
    """
    # Create two time slots
    ts1 = TimeSlot.objects.create(
        start_time=timezone.now(),
        end_time=timezone.now() + timezone.timedelta(hours=1)
    )
    ts2 = TimeSlot.objects.create(
        start_time=timezone.now() + timezone.timedelta(hours=2),
        end_time=timezone.now() + timezone.timedelta(hours=3)
    )

    # Create two meetings in non-sorted order of score
    meeting_low_score = Meeting.objects.create(attendee1=test_user, attendee2=other_user, time_slot=ts1, room=room, score=10)
    meeting_high_score = Meeting.objects.create(attendee1=other_user, attendee2=test_user, time_slot=ts2, room=room, score=20)

    api_client.force_authenticate(user=test_user)
    url = reverse('meeting-list')
    response = api_client.get(url, {'ordering': '-score'})

    assert response.status_code == 200
    results = response.data['results']
    assert len(results) == 2
    # Check that the meeting with the higher score comes first
    assert [m['id'] for m in results] == [meeting_high_score.id, meeting_low_score.id]


def test_meeting_is_future_filter_works(api_client, test_user, other_user, room):
    """
    GIVEN a user has meetings in the past and future
    WHEN they make a GET request with the is_future=true filter
    THEN they should only receive a list of meetings in the future.
    """
    # Create a time slot in the past
    past_ts = TimeSlot.objects.create(
        start_time=timezone.now() - timezone.timedelta(days=1),
        end_time=timezone.now() - timezone.timedelta(days=1, hours=-1)
    )
    # Create a time slot in the future
    future_ts = TimeSlot.objects.create(
        start_time=timezone.now() + timezone.timedelta(days=1),
        end_time=timezone.now() + timezone.timedelta(days=1, hours=1)
    )

    # Create one meeting in the past and one in the future
    past_meeting = Meeting.objects.create(attendee1=test_user, attendee2=other_user, time_slot=past_ts, room=room)
    future_meeting = Meeting.objects.create(attendee1=other_user, attendee2=test_user, time_slot=future_ts, room=room)

    api_client.force_authenticate(user=test_user)
    url = reverse('meeting-list')
    response = api_client.get(url, {'is_future': 'true'})

    assert response.status_code == 200
    results = response.data['results']
    assert len(results) == 1
    assert results[0]['id'] == future_meeting.id


def test_clear_interests_action_works(api_client, test_user, skills):
    """
    GIVEN an authenticated user with several interests
    WHEN they send a DELETE request to the clear_interests endpoint
    THEN their profile's interests should be cleared and they receive a 204 NO CONTENT status.
    """
    # Add all skills from the fixture to the user's profile
    test_user.profile.interests.set(skills)
    assert test_user.profile.interests.count() == 3

    api_client.force_authenticate(user=test_user)
    url = reverse('user-profile-clear-interests')

    response = api_client.delete(url)

    assert response.status_code == 204

    # Verify the interests are gone from the database
    test_user.profile.refresh_from_db()
    assert test_user.profile.interests.count() == 0


def test_timeslot_has_available_rooms_filter_works(api_client, test_user, other_user):
    """
    GIVEN two time slots, one with all rooms booked and one with available rooms
    WHEN a GET request is made with the has_available_rooms=true filter
    THEN only the time slot with available rooms should be returned.
    """
    # 1. Setup: Create 2 rooms
    room1 = Room.objects.create(name="Room 1")
    room2 = Room.objects.create(name="Room 2")

    # 2. Setup: Create one full time slot and one with availability
    full_slot = TimeSlot.objects.create(start_time=timezone.now(), end_time=timezone.now() + timezone.timedelta(hours=1))
    available_slot = TimeSlot.objects.create(start_time=timezone.now() + timezone.timedelta(hours=1), end_time=timezone.now() + timezone.timedelta(hours=2))

    # 3. Setup: Create more users to fill the slot
    user3 = User.objects.create_user(username='user3')
    user4 = User.objects.create_user(username='user4')

    # 4. Setup: Fill the 'full_slot' with two meetings (one for each room)
    Meeting.objects.create(attendee1=test_user, attendee2=other_user, time_slot=full_slot, room=room1)
    Meeting.objects.create(attendee1=user3, attendee2=user4, time_slot=full_slot, room=room2)

    # 5. Setup: Add only one meeting to the 'available_slot'
    Meeting.objects.create(attendee1=test_user, attendee2=other_user, time_slot=available_slot, room=room1)

    api_client.force_authenticate(user=test_user)
    url = reverse('timeslot-list')
    response = api_client.get(url, {'has_available_rooms': 'true'})

    assert response.status_code == 200
    results = response.data['results']
    assert len(results) == 1
    assert results[0]['id'] == available_slot.id


def test_timeslot_is_user_available_filter_works(api_client, test_user):
    """
    GIVEN a user is available for one time slot but not another
    WHEN they make a GET request with the is_user_available=true filter
    THEN only the time slot they are available for should be returned.
    """
    # 1. Setup: Create two time slots
    available_slot = TimeSlot.objects.create(start_time=timezone.now(), end_time=timezone.now() + timezone.timedelta(hours=1))
    unavailable_slot = TimeSlot.objects.create(start_time=timezone.now() + timezone.timedelta(hours=1), end_time=timezone.now() + timezone.timedelta(hours=2))

    # 2. Setup: Mark the user as available for only one slot
    UserAvailability.objects.create(user=test_user, time_slot=available_slot)

    api_client.force_authenticate(user=test_user)
    url = reverse('timeslot-list')
    response = api_client.get(url, {'is_user_available': 'true'})

    assert response.status_code == 200
    results = response.data['results']
    assert len(results) == 1
    assert results[0]['id'] == available_slot.id


def test_cancel_meeting_permissions(api_client, test_user, other_user, time_slot, room):
    """
    GIVEN a meeting exists between two users
    WHEN a third user tries to cancel it, they should be denied.
    WHEN one of the attendees tries to cancel it, it should succeed.
    """
    # 1. Setup: Create a meeting between test_user and other_user
    meeting = Meeting.objects.create(
        attendee1=test_user, attendee2=other_user, time_slot=time_slot, room=room
    )

    # 2. Setup: Create a third user who is not part of the meeting
    third_user = User.objects.create_user(username='thirduser', password='password123')

    # 3. Test Failure Case: The third user cannot cancel the meeting
    api_client.force_authenticate(user=third_user)
    url = reverse('meeting-cancel', kwargs={'pk': meeting.pk})
    response = api_client.post(url)
    assert response.status_code == 404, "User should not be able to find a meeting they are not part of"
    assert Meeting.objects.filter(pk=meeting.pk).exists(), "Meeting should not be deleted"

    # 4. Test Success Case: An actual attendee can cancel the meeting
    api_client.force_authenticate(user=test_user)
    response = api_client.post(url)
    assert response.status_code == 204, "Attendee should be able to cancel their meeting"
    assert not Meeting.objects.filter(pk=meeting.pk).exists(), "Meeting should be deleted"


def test_email_sent_on_meeting_cancellation(api_client, test_user, other_user, time_slot, room):
    """
    GIVEN a meeting between two users
    WHEN one user cancels the meeting
    THEN an email notification should be sent to the other attendee.
    """
    meeting = Meeting.objects.create(
        attendee1=test_user, attendee2=other_user, time_slot=time_slot, room=room
    )

    api_client.force_authenticate(user=test_user)
    url = reverse('meeting-cancel', kwargs={'pk': meeting.pk})
    api_client.post(url)

    assert Notification.objects.filter(user=other_user, event_type=Notification.EventType.MEETING_CANCELLED).exists()


def test_skill_merge_action_works(api_client, admin_user, test_user, other_user):
    """
    GIVEN an admin user, two skills, and users with one of those skills
    WHEN the admin merges the source skill into the target skill
    THEN the source skill should be deleted and all user interests should be migrated.
    """
    # 1. Setup: Create the skills to be merged
    source_skill = Skill.objects.create(name="AI")
    target_skill = Skill.objects.create(name="Artificial Intelligence")

    # 2. Setup: Assign the source skill to two different users
    test_user.profile.interests.add(source_skill)
    other_user.profile.interests.add(source_skill)

    assert test_user.profile.interests.count() == 1
    assert other_user.profile.interests.count() == 1

    # 3. Perform the merge action
    api_client.force_authenticate(user=admin_user)
    url = reverse('skill-merge', kwargs={'pk': target_skill.pk})
    payload = {'source_skill_id': source_skill.pk}
    response = api_client.post(url, data=payload)

    # 4. Assert the results
    assert response.status_code == 200
    assert not Skill.objects.filter(pk=source_skill.pk).exists(), "Source skill should be deleted"

    # 5. Verify user interests have been migrated
    test_user.profile.refresh_from_db()
    other_user.profile.refresh_from_db()
    assert test_user.profile.interests.count() == 1
    assert test_user.profile.interests.first() == target_skill
    assert other_user.profile.interests.first() == target_skill


def test_skill_merge_with_self_fails(api_client, admin_user, skills):
    """
    GIVEN an admin user
    WHEN they attempt to merge a skill into itself
    THEN they should receive a 400 BAD REQUEST error.
    """
    target_skill = skills[0]
    api_client.force_authenticate(user=admin_user)
    url = reverse('skill-merge', kwargs={'pk': target_skill.pk})
    payload = {'source_skill_id': target_skill.pk} # Merging with self
    response = api_client.post(url, data=payload)
    assert response.status_code == 400


def test_non_admin_cannot_merge_skill(api_client, test_user, skills):
    """
    GIVEN a non-admin user
    WHEN they attempt to merge skills
    THEN they should receive a 403 FORBIDDEN error.
    """
    api_client.force_authenticate(user=test_user)
    url = reverse('skill-merge', kwargs={'pk': skills[0].pk})
    payload = {'source_skill_id': skills[1].pk}
    response = api_client.post(url, data=payload)
    assert response.status_code == 403
    

def test_propose_reschedule_success(api_client, test_user, other_user, room):
    """
    GIVEN a meeting between two users
    WHEN one user proposes a new time slot
    THEN a MeetingRescheduleProposal object should be created.
    """
    # 1. Setup: Create the original meeting and a new time slot to propose
    original_slot = TimeSlot.objects.create(start_time=timezone.now(), end_time=timezone.now() + timezone.timedelta(hours=1))
    proposed_slot = TimeSlot.objects.create(start_time=timezone.now() + timezone.timedelta(days=1), end_time=timezone.now() + timezone.timedelta(days=1, hours=1))
    
    meeting = Meeting.objects.create(attendee1=test_user, attendee2=other_user, time_slot=original_slot, room=room)

    # 2. Perform the action
    api_client.force_authenticate(user=test_user)
    url = reverse('meeting-propose-reschedule', kwargs={'pk': meeting.pk})
    # The payload key now matches the updated serializer field name.
    payload = {'proposed_time_slot': proposed_slot.pk}
    response = api_client.post(url, data=payload)

    # 3. Assert the outcome
    assert response.status_code == 201
    assert MeetingRescheduleProposal.objects.count() == 1
    
    proposal = MeetingRescheduleProposal.objects.first()
    assert proposal.meeting == meeting
    assert proposal.proposer == test_user
    assert proposal.proposed_time_slot == proposed_slot
    assert proposal.status == MeetingRescheduleProposal.Status.PENDING


def test_propose_reschedule_same_slot_fails(api_client, test_user, other_user, room, time_slot):
    """
    GIVEN a meeting
    WHEN a user tries to propose the same time slot
    THEN they should receive a 400 BAD REQUEST error.
    """
    meeting = Meeting.objects.create(attendee1=test_user, attendee2=other_user, time_slot=time_slot, room=room)
    api_client.force_authenticate(user=test_user)
    url = reverse('meeting-propose-reschedule', kwargs={'pk': meeting.pk})
    payload = {'proposed_time_slot': time_slot.pk} # Proposing the same slot
    response = api_client.post(url, data=payload)
    assert response.status_code == 400
    assert "Cannot propose the same time slot" in str(response.data)


def test_accept_reschedule_proposal(api_client, test_user, other_user, room):
    """
    GIVEN a meeting and a reschedule proposal from test_user to other_user
    WHEN other_user (the receiver) accepts the proposal
    THEN the meeting's time slot should be updated and the proposal status changed.
    """
    # 1. Setup: Create the original meeting and a new time slot to propose
    original_slot = TimeSlot.objects.create(start_time=timezone.now(), end_time=timezone.now() + timezone.timedelta(hours=1))
    proposed_slot = TimeSlot.objects.create(start_time=timezone.now() + timezone.timedelta(days=1), end_time=timezone.now() + timezone.timedelta(days=1, hours=1))
    meeting = Meeting.objects.create(attendee1=test_user, attendee2=other_user, time_slot=original_slot, room=room)
    proposal = MeetingRescheduleProposal.objects.create(meeting=meeting, proposer=test_user, proposed_time_slot=proposed_slot)

    # 2. Test Failure Case: The proposer cannot accept their own proposal
    api_client.force_authenticate(user=test_user)
    url = reverse('reschedule-proposal-accept', kwargs={'pk': proposal.pk})
    response = api_client.post(url)
    assert response.status_code == 404, "Proposer should not be able to see/accept their own proposal"

    # 3. Test Success Case: The receiver accepts the proposal
    api_client.force_authenticate(user=other_user)
    response = api_client.post(url)

    # 4. Assert the outcome
    assert response.status_code == 200
    assert response.data['status'] == 'Proposal accepted and meeting rescheduled.'

    # 5. Verify the database state
    meeting.refresh_from_db()
    proposal.refresh_from_db()
    assert meeting.time_slot == proposed_slot, "Meeting should be moved to the new time slot"
    assert proposal.status == MeetingRescheduleProposal.Status.ACCEPTED, "Proposal status should be ACCEPTED"


def test_notification_sent_on_proposal_acceptance(api_client, test_user, other_user, room):
    """
    GIVEN a reschedule proposal from other_user to test_user
    WHEN test_user accepts the proposal
    THEN a notification should be created for other_user (the proposer).
    """
    original_slot = TimeSlot.objects.create(start_time=timezone.now(), end_time=timezone.now() + timezone.timedelta(hours=1))
    proposed_slot = TimeSlot.objects.create(start_time=timezone.now() + timezone.timedelta(days=1), end_time=timezone.now() + timezone.timedelta(days=1, hours=1))
    meeting = Meeting.objects.create(attendee1=test_user, attendee2=other_user, time_slot=original_slot, room=room)
    proposal = MeetingRescheduleProposal.objects.create(meeting=meeting, proposer=other_user, proposed_time_slot=proposed_slot)

    # test_user (the receiver) accepts the proposal
    api_client.force_authenticate(user=test_user)
    url = reverse('reschedule-proposal-accept', kwargs={'pk': proposal.pk})
    response = api_client.post(url)

    assert response.status_code == 200
    assert Notification.objects.filter(
        user=other_user,
        event_type=Notification.EventType.PROPOSAL_ACCEPTED
    ).exists()


def test_my_proposals_viewset_returns_sent_and_received(api_client, test_user, other_user, room):
    """
    GIVEN a user has sent one proposal and received another
    WHEN they request the my-proposals list endpoint
    THEN they should receive both proposals with the correct 'direction' field.
    """
    # 1. Setup: Create another user for the second meeting
    third_user = User.objects.create_user(username='thirduser', password='password123')

    # 2. Setup: Create a "sent" proposal (test_user -> other_user)
    sent_meeting = Meeting.objects.create(attendee1=test_user, attendee2=other_user, time_slot=TimeSlot.objects.create(start_time=timezone.now()), room=room)
    sent_proposal = MeetingRescheduleProposal.objects.create(meeting=sent_meeting, proposer=test_user, proposed_time_slot=TimeSlot.objects.create(start_time=timezone.now() + timezone.timedelta(days=1)))

    # 3. Setup: Create a "received" proposal (third_user -> test_user)
    received_meeting = Meeting.objects.create(attendee1=third_user, attendee2=test_user, time_slot=TimeSlot.objects.create(start_time=timezone.now() + timezone.timedelta(hours=1)), room=room)
    received_proposal = MeetingRescheduleProposal.objects.create(meeting=received_meeting, proposer=third_user, proposed_time_slot=TimeSlot.objects.create(start_time=timezone.now() + timezone.timedelta(days=2)))

    # 4. Perform the API call
    api_client.force_authenticate(user=test_user)
    url = reverse('my-proposal-list')
    response = api_client.get(url)

    # 5. Assert the outcome
    assert response.status_code == 200
    results = response.data['results']
    assert len(results) == 2

    directions = {p['direction'] for p in results}
    assert directions == {'sent', 'received'}, "Response should contain both sent and received proposals"


def test_whats_on_now_viewset(api_client, test_user, other_user, room):
    """
    GIVEN meetings in the past, present, and future
    WHEN a GET request is made to the whats-on-now endpoint
    THEN only the meeting currently in progress should be returned.
    """
    now = timezone.now()

    # 1. Setup: Create time slots and meetings for different time periods
    past_slot = TimeSlot.objects.create(start_time=now - timezone.timedelta(hours=2), end_time=now - timezone.timedelta(hours=1))
    present_slot = TimeSlot.objects.create(start_time=now - timezone.timedelta(minutes=30), end_time=now + timezone.timedelta(minutes=30))
    future_slot = TimeSlot.objects.create(start_time=now + timezone.timedelta(hours=1), end_time=now + timezone.timedelta(hours=2))

    Meeting.objects.create(attendee1=test_user, attendee2=other_user, time_slot=past_slot, room=room)
    present_meeting = Meeting.objects.create(attendee1=test_user, attendee2=other_user, time_slot=present_slot, room=room)
    Meeting.objects.create(attendee1=test_user, attendee2=other_user, time_slot=future_slot, room=room)

    # 2. Perform the API call
    api_client.force_authenticate(user=test_user)
    url = reverse('whats-on-now-list')
    response = api_client.get(url)

    assert response.status_code == 200
    results = response.data['results']
    assert len(results) == 1
    assert results[0]['id'] == present_meeting.id


def test_public_profile_viewset(api_client, test_user, other_user):
    """
    GIVEN one user is checked in and another is not
    WHEN a GET request is made to the public profiles endpoint
    THEN only the checked-in user's profile should be returned.
    """
    # 1. Setup: Check in one user, but not the other
    test_user.profile.checked_in = True
    test_user.profile.save()

    # 2. Perform the API call
    api_client.force_authenticate(user=test_user)
    url = reverse('public-profile-list')
    response = api_client.get(url)

    assert response.status_code == 200
    results = response.data['results']
    assert len(results) == 1
    assert results[0]['username'] == test_user.username


def test_admin_can_check_in_user(api_client, admin_user, test_user):
    """
    GIVEN an admin user and a regular user who is not checked in
    WHEN the admin makes a POST request to the check-in endpoint for the user
    THEN the user's profile should be updated to checked_in=True.
    """
    assert not test_user.profile.checked_in
    api_client.force_authenticate(user=admin_user)
    url = reverse('user-admin-check-in', kwargs={'pk': test_user.pk})
    response = api_client.post(url)

    assert response.status_code == 200
    test_user.profile.refresh_from_db()
    assert test_user.profile.checked_in


def test_non_admin_cannot_check_in_user(api_client, test_user, other_user):
    """
    GIVEN a non-admin user
    WHEN they attempt to check in another user
    THEN they should receive a 403 FORBIDDEN error.
    """
    api_client.force_authenticate(user=test_user)
    url = reverse('user-admin-check-in', kwargs={'pk': other_user.pk})
    response = api_client.post(url)
    assert response.status_code == 403


def test_leaderboard_viewset(api_client, test_user, other_user, room):
    """
    GIVEN several users with a different number of meetings
    WHEN a GET request is made to the leaderboard endpoint
    THEN a ranked list of users should be returned, from most to least meetings.
    """
    # 1. Setup: Create users and meetings to establish a clear ranking
    user_most_meetings = other_user  # Will have 2 meetings
    user_one_meeting = test_user      # Will have 1 meeting
    user_zero_meetings = User.objects.create_user(username='zeromeetings') # Will have 0 meetings
    user_also_one_meeting = User.objects.create_user(username='tempuser')

    # Meeting 1: most_meetings <-> one_meeting
    slot1 = TimeSlot.objects.create(start_time=timezone.now(), end_time=timezone.now() + timezone.timedelta(hours=1))
    Meeting.objects.create(attendee1=user_most_meetings, attendee2=user_one_meeting, time_slot=slot1, room=room)

    # Meeting 2: most_meetings <-> another user, to give them a total of 2
    slot2 = TimeSlot.objects.create(start_time=timezone.now() + timezone.timedelta(hours=1), end_time=timezone.now() + timezone.timedelta(hours=2))
    Meeting.objects.create(attendee1=user_most_meetings, attendee2=user_also_one_meeting, time_slot=slot2, room=room)

    # 2. Perform the API call
    api_client.force_authenticate(user=test_user)
    url = reverse('leaderboard-list')
    response = api_client.get(url)

    assert response.status_code == 200
    results = response.data['results']
    assert len(results) == 3, "Expected 3 users with meetings on the leaderboard"
    
    # Expected order: other_user (2), test_user (1), tempuser (1) - with alphabetical tie-breaking
    usernames = [r['username'] for r in results]
    counts = [r['meeting_count'] for r in results]

    assert usernames[0] == user_most_meetings.username
    assert counts[0] == 2

    # The next two have 1 meeting each, so they should be sorted by username
    assert sorted(usernames[1:]) == [user_one_meeting.username, user_also_one_meeting.username]
    assert counts[1] == 1
    assert counts[2] == 1


def test_my_stats_view(api_client, test_user, other_user, room):
    """
    GIVEN a user with a specific number of meetings and rank
    WHEN they make a GET request to the my-stats endpoint
    THEN they should receive their correct meeting count and rank.
    """
    # 1. Setup: Create a user with more meetings than test_user to establish a rank
    top_user = other_user
    Meeting.objects.create(
        attendee1=top_user, attendee2=test_user,
        time_slot=TimeSlot.objects.create(start_time=timezone.now()), room=room
    )
    Meeting.objects.create(
        attendee1=top_user, attendee2=User.objects.create_user('tempuser'),
        time_slot=TimeSlot.objects.create(start_time=timezone.now() + timezone.timedelta(hours=1)), room=room
    )

    # 2. Perform the API call for test_user
    api_client.force_authenticate(user=test_user)
    url = reverse('my-stats')
    response = api_client.get(url)

    assert response.status_code == 200
    assert response.data['username'] == test_user.username
    assert response.data['meeting_count'] == 1
    assert response.data['rank'] == 2, "test_user should be ranked second"


def test_recommended_matches_view(api_client, test_user, skills, room):
    """
    GIVEN a user and several potential matches with varying scores and statuses
    WHEN they request the recommended-matches endpoint
    THEN they should receive a correctly ranked list of checked-in users
    with whom they do not already have a meeting.
    """
    # 1. Setup: Create users and assign interests to create a clear ranking
    # test_user has Python and Django interests
    test_user.profile.interests.add(skills[0], skills[1])
    test_user.profile.checked_in = True
    test_user.profile.save()

    # high_match_user: 2 shared interests, checked in
    high_match_user = User.objects.create_user('highmatch')
    high_match_user.profile.interests.add(skills[0], skills[1])
    high_match_user.profile.checked_in = True
    high_match_user.profile.save()

    # low_match_user: 1 shared interest, checked in
    low_match_user = User.objects.create_user('lowmatch')
    low_match_user.profile.interests.add(skills[0]) # Python
    low_match_user.profile.checked_in = True
    low_match_user.profile.save()

    # not_checked_in_user: 2 shared interests, but not checked in
    not_checked_in_user = User.objects.create_user('notcheckedin')
    not_checked_in_user.profile.interests.add(skills[0], skills[1])
    not_checked_in_user.profile.save()

    # existing_meeting_user: 2 shared interests, but already has a meeting
    existing_meeting_user = User.objects.create_user('hasmeeting')
    existing_meeting_user.profile.interests.add(skills[0], skills[1])
    existing_meeting_user.profile.checked_in = True
    existing_meeting_user.profile.save()
    Meeting.objects.create(attendee1=test_user, attendee2=existing_meeting_user, time_slot=TimeSlot.objects.create(start_time=timezone.now()), room=room)

    # 2. Perform the API call
    api_client.force_authenticate(user=test_user)
    url = reverse('recommended-matches')
    response = api_client.get(url)

    # 3. Assert the outcome
    assert response.status_code == 200
    results = response.data['results']
    assert len(results) == 2, "Should only return checked-in users without existing meetings"
    
    # Score: high_match (2 interest + 3 feedback) = 5. low_match (1 interest + 3 feedback) = 4
    assert [r['user']['username'] for r in results] == ['highmatch', 'lowmatch'], "Results should be ordered by match score"
    assert [r['match_score'] for r in results] == [5.0, 4.0]


def test_request_meeting_action_sends_email(api_client, test_user, other_user):
    """
    GIVEN a user requests a meeting with another checked-in user
    WHEN they POST to the request-meeting endpoint
    THEN an email should be sent to the target user.
    """
    from django.core import mail

    # The target user must be checked in to be visible in the viewset
    other_user.profile.checked_in = True
    other_user.profile.save()

    api_client.force_authenticate(user=test_user)
    url = reverse('public-profile-request-meeting', kwargs={'pk': other_user.profile.pk})
    response = api_client.post(url)

    assert response.status_code == 200
    assert len(mail.outbox) == 1
    email = mail.outbox[0]
    assert email.to == [other_user.email]
    assert f"Meeting Request from {test_user.username}" in email.subject


def test_request_meeting_with_self_fails(api_client, test_user):
    """
    GIVEN a user
    WHEN they attempt to request a meeting with themselves
    THEN they should receive a 400 BAD REQUEST error.
    """
    api_client.force_authenticate(user=test_user)
    url = reverse('public-profile-request-meeting', kwargs={'pk': test_user.profile.pk})
    response = api_client.post(url)
    assert response.status_code == 400
    assert "You cannot request a meeting with yourself" in response.data['error']


def test_my_event_feed_view(api_client, test_user, other_user, room):
    """
    GIVEN a user has various activities (meetings, proposals)
    WHEN they request their event feed
    THEN they should receive a chronologically sorted list of these events.
    """
    # 1. Setup: Create a meeting (will be the "latest" event by start_time)
    latest_time = timezone.now()
    meeting = Meeting.objects.create(
        attendee1=test_user, attendee2=other_user,
        time_slot=TimeSlot.objects.create(start_time=latest_time),
        room=room
    )

    # 2. Setup: Create a proposal (will be the "earliest" event by created_at)
    proposal = MeetingRescheduleProposal.objects.create(
        meeting=meeting, proposer=test_user,
        proposed_time_slot=TimeSlot.objects.create(start_time=latest_time + timezone.timedelta(days=1))
    )
    proposal.created_at = latest_time - timezone.timedelta(hours=1)
    proposal.save()

    # 3. Perform the API call
    api_client.force_authenticate(user=test_user)
    url = reverse('my-feed')
    response = api_client.get(url)

    assert response.status_code == 200
    results = response.data['results']
    assert len(results) == 2
    # Verify the feed is sorted descending by timestamp
    assert results[0]['event_type'] == 'MEETING_SCHEDULED'
    assert results[1]['event_type'] == 'PROPOSAL_SENT'


def test_my_event_summary_view(api_client, test_user, other_user, skills, room):
    """
    GIVEN a user with a defined set of activities
    WHEN they request their event summary
    THEN they should receive the correct counts for meetings, pending proposals,
    and a list of their top interests.
    """
    # 1. Setup: Create a meeting for the user
    meeting = Meeting.objects.create(attendee1=test_user, attendee2=other_user, time_slot=TimeSlot.objects.create(start_time=timezone.now()), room=room)

    # 2. Setup: Create a pending proposal *for* the user
    MeetingRescheduleProposal.objects.create(meeting=meeting, proposer=other_user, proposed_time_slot=TimeSlot.objects.create(start_time=timezone.now() + timezone.timedelta(days=1)))

    # 3. Setup: Assign interests to the user
    test_user.profile.interests.set(skills) # Python, Django, React

    # 4. Perform the API call
    api_client.force_authenticate(user=test_user)
    url = reverse('my-summary')
    response = api_client.get(url)

    assert response.status_code == 200
    assert response.data['total_meetings'] == 1
    assert response.data['pending_proposals_count'] == 1
    assert response.data['top_interests'] == ['Python', 'Django', 'React']


def test_meeting_feedback_workflow(api_client, test_user, other_user, time_slot, room):
    """
    Tests the full workflow of submitting and viewing meeting feedback,
    including permissions and validation.
    """
    # 1. Setup: Create a meeting
    meeting = Meeting.objects.create(
        attendee1=test_user, attendee2=other_user, time_slot=time_slot, room=room
    )
    feedback_url = reverse('meeting-feedback', kwargs={'pk': meeting.pk})

    # 2. Test Failure: A non-attendee cannot submit feedback
    third_user = User.objects.create_user('thirduser')
    api_client.force_authenticate(user=third_user)
    response = api_client.post(feedback_url, {'rating': 5})
    assert response.status_code == 404, "A non-attendee should not be able to find the meeting."

    # 3. Test Success: An attendee can submit feedback
    api_client.force_authenticate(user=test_user)
    payload = {'rating': 5, 'comments': 'Excellent conversation!'}
    response = api_client.post(feedback_url, data=payload)
    assert response.status_code == 201
    assert response.data['rating'] == 5
    assert MeetingFeedback.objects.count() == 1

    # 4. Test Failure: The same attendee cannot submit feedback twice
    response = api_client.post(feedback_url, data=payload)
    assert response.status_code == 400
    assert "already submitted feedback" in str(response.data)

    # 5. Test Success: An attendee can view all feedback for the meeting
    api_client.force_authenticate(user=other_user)
    response = api_client.get(feedback_url)
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['rating'] == 5


def test_block_unblock_workflow(api_client, test_user, other_user):
    """
    Tests the full workflow for blocking and unblocking a user,
    and verifies that blocking prevents meeting requests.
    """
    # The user to be blocked must be checked in to be visible in the viewset
    other_user.profile.checked_in = True
    other_user.profile.save()

    # 1. Block the user
    api_client.force_authenticate(user=test_user)
    block_url = reverse('public-profile-block', kwargs={'pk': other_user.profile.pk})
    response = api_client.post(block_url)
    assert response.status_code == 200
    assert test_user.profile.blocked_users.filter(pk=other_user.profile.pk).exists()

    # 2. Verify block prevents meeting requests
    request_url = reverse('public-profile-request-meeting', kwargs={'pk': other_user.profile.pk})
    response = api_client.post(request_url)
    assert response.status_code == 403
    assert "user you have blocked" in response.data['error']

    # 3. Unblock the user
    unblock_url = reverse('public-profile-unblock', kwargs={'pk': other_user.profile.pk})
    response = api_client.post(unblock_url)
    assert response.status_code == 200
    assert not test_user.profile.blocked_users.filter(pk=other_user.profile.pk).exists()

    # 4. Verify unblock allows meeting requests again
    response = api_client.post(request_url)
    assert response.status_code == 200, "Meeting request should now succeed"


def test_notification_viewset_workflow(api_client, test_user, other_user):
    """
    Tests the full workflow for notifications: listing, permissions,
    and marking as read.
    """
    # 1. Setup: Create notifications for two different users
    my_notification = Notification.objects.create(user=test_user, event_type='MTG_CNL', message='Your meeting was cancelled.')
    other_notification = Notification.objects.create(user=other_user, event_type='PRP_RCV', message='You have a proposal.')

    # 2. Test List & Permissions: User can only see their own notification
    api_client.force_authenticate(user=test_user)
    list_url = reverse('notification-list')
    response = api_client.get(list_url)
    assert response.status_code == 200
    results = response.data['results']
    assert len(results) == 1
    assert results[0]['id'] == my_notification.id

    # 3. Test Mark as Read (single): User can mark their notification as read
    assert not my_notification.is_read
    mark_one_url = reverse('notification-mark-as-read', kwargs={'pk': my_notification.pk})
    response = api_client.post(mark_one_url)
    assert response.status_code == 204
    my_notification.refresh_from_db()
    assert my_notification.is_read

    # 4. Test Mark as Read Permissions: User cannot mark another's notification as read
    mark_other_url = reverse('notification-mark-as-read', kwargs={'pk': other_notification.pk})
    response = api_client.post(mark_other_url)
    assert response.status_code == 404 # Cannot find it in their queryset

    # 5. Test Mark All as Read
    # Create more unread notifications for the user
    Notification.objects.create(user=test_user, event_type='PRP_ACC', message='Proposal accepted.')
    Notification.objects.create(user=test_user, event_type='PRP_REJ', message='Proposal rejected.')
    assert test_user.notifications.filter(is_read=False).count() == 2
    mark_all_url = reverse('notification-mark-all-as-read')
    response = api_client.post(mark_all_url)
    assert response.status_code == 204
    assert test_user.notifications.filter(is_read=False).count() == 0


def test_snooze_notifications_workflow(api_client, test_user, other_user, room):
    """
    Tests the full workflow for snoozing and unsnoozing notifications.
    """
    # 1. Setup: Create a meeting to be cancelled
    meeting = Meeting.objects.create(attendee1=test_user, attendee2=other_user, time_slot=TimeSlot.objects.create(start_time=timezone.now()), room=room)
    cancel_url = reverse('meeting-cancel', kwargs={'pk': meeting.pk})

    # 2. Snooze notifications for the target user (other_user)
    api_client.force_authenticate(user=other_user)
    snooze_url = reverse('user-profile-snooze')
    response = api_client.post(snooze_url, {'duration_hours': 24})
    assert response.status_code == 200
    other_user.profile.refresh_from_db()
    assert other_user.profile.notifications_snoozed_until is not None

    # 3. Trigger a notification event (cancel the meeting)
    api_client.force_authenticate(user=test_user)
    api_client.post(cancel_url)

    # 4. Assert that NO notification was created for the snoozed user
    assert not Notification.objects.filter(user=other_user).exists()

    # 5. Un-snooze notifications for the target user
    api_client.force_authenticate(user=other_user)
    unsnooze_url = reverse('user-profile-unsnooze')
    response = api_client.post(unsnooze_url)
    assert response.status_code == 204
    other_user.profile.refresh_from_db()
    assert other_user.profile.notifications_snoozed_until is None

    # 6. Trigger another notification event and assert it IS created now
    new_meeting = Meeting.objects.create(attendee1=test_user, attendee2=other_user, time_slot=TimeSlot.objects.create(start_time=timezone.now()), room=room)
    api_client.force_authenticate(user=test_user)
    api_client.post(reverse('meeting-cancel', kwargs={'pk': new_meeting.pk}))
    assert Notification.objects.filter(user=other_user).count() == 1


def test_blocked_users_list_in_profile(api_client, test_user, other_user):
    """
    GIVEN a user has blocked another user
    WHEN they make a GET request to their own profile endpoint
    THEN the blocked user should appear in the 'blocked_users' list.
    """
    # 1. Setup: Block the other user
    test_user.profile.blocked_users.add(other_user.profile)

    # 2. Perform the API call to get the profile
    api_client.force_authenticate(user=test_user)
    url = reverse('user-profile')
    response = api_client.get(url)

    # 3. Assert the outcome
    assert response.status_code == 200
    assert 'blocked_users' in response.data
    assert len(response.data['blocked_users']) == 1
    assert response.data['blocked_users'][0]['username'] == other_user.username