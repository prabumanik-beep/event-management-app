"""
A simplified example of an intelligent meeting scheduler using Google OR-Tools.

This script models the problem of scheduling 1-on-1 meetings between attendees
at a conference based on shared interests to maximize attendee satisfaction.

To run this, you'll need to install Google's OR-Tools:
pip install ortools
"""

import collections
from ortools.sat.python import cp_model

# Django-specific imports. This script must now be run within the Django context.
from django.contrib.auth import get_user_model
from django.db.models import Avg, Q
from .models import (Meeting, MeetingFeedback, Profile, Room, TimeSlot)
from .utils import calculate_average_ratings_for_users

User = get_user_model()

def calculate_interest_score(person1_data, person2_data):
    """
    Calculates a score based on shared interests, special roles, and past feedback.
    Prioritizes mentor-mentee matches with a large bonus.
    """
    # Base score from shared interests
    base_score = len(set(person1_data['interests']) & set(person2_data['interests']))

    # Role-based bonus score
    role_bonus = 0
    p1_role = person1_data.get('role')
    p2_role = person2_data.get('role')

    # Use the Role enum from the model for safe comparisons
    if (p1_role == Profile.Role.MENTOR and p2_role == Profile.Role.MENTEE) or \
       (p1_role == Profile.Role.MENTEE and p2_role == Profile.Role.MENTOR):
        role_bonus = 50  # High priority bonus for mentor-mentee match

    # Feedback-based bonus. We use the average rating a user has RECEIVED.
    # This rewards users who have been good meeting partners in the past.
    # A user with an avg rating of 5 gets a bonus of 5. A user with 1 gets 1.
    p1_rating = person1_data.get('avg_rating_received', 3.0)
    p2_rating = person2_data.get('avg_rating_received', 3.0)
    feedback_bonus = (p1_rating + p2_rating) / 2 # Average their rating bonus

    return base_score + role_bonus + feedback_bonus

def solve_meeting_schedule():
    """Creates and solves the meeting scheduling model using data from the database."""
    # 1. Fetch real data from Django models

    # Get all relevant objects and create mappings from DB ID -> solver index
    all_time_slots = list(TimeSlot.objects.all())
    slot_map = {slot.id: i for i, slot in enumerate(all_time_slots)}

    all_rooms = list(Room.objects.all())
    room_map = {room.id: i for i, room in enumerate(all_rooms)}

    all_users_with_profiles_qs = User.objects.filter(profile__isnull=False)
    all_user_ids = [u.id for u in all_users_with_profiles_qs]

    # Use the new utility function to get average ratings
    avg_ratings_received = calculate_average_ratings_for_users(all_user_ids)

    # Fetch users who have marked availability and have a profile with interests
    all_people_qs = User.objects.filter(
        available_slots__isnull=False, profile__isnull=False
    ).prefetch_related(
        'profile__interests', 'available_slots', 'profile__blocked_users', 'profile__blocked_by'
    ).distinct()
    all_people = list(all_people_qs)
    people_map = {person.id: i for i, person in enumerate(all_people)}

    # Structure the data into a format the solver can use
    attendees_data = collections.defaultdict(dict)
    for person in all_people:
        person_idx = people_map[person.id]
        interests = [interest.name for interest in person.profile.interests.all()]
        availability = [slot_map[slot.id] for slot in person.available_slots.all() if slot.id in slot_map]
        attendees_data[person_idx]['interests'] = interests
        attendees_data[person_idx]['availability'] = availability
        attendees_data[person_idx]['role'] = person.profile.role
        attendees_data[person_idx]['avg_rating_received'] = avg_ratings_received.get(person.id, 3.0)

    num_people = len(all_people)
    num_slots = len(all_time_slots)
    num_rooms = len(all_rooms)

    # Create a set of blocked pairs (p1_idx, p2_idx) where p1_idx < p2_idx
    blocked_pairs = set()
    for person in all_people:
        p1_idx = people_map[person.id]
        # People this person has blocked
        for blocked_profile in person.profile.blocked_users.all():
            if blocked_profile.user_id in people_map:
                p2_idx = people_map[blocked_profile.user_id]
                blocked_pairs.add(tuple(sorted((p1_idx, p2_idx))))
        # People who have blocked this person
        for blocking_profile in person.profile.blocked_by.all():
            if blocking_profile.user_id in people_map:
                p2_idx = people_map[blocking_profile.user_id]
                blocked_pairs.add(tuple(sorted((p1_idx, p2_idx))))

    if num_people < 2 or num_slots == 0 or num_rooms == 0:
        return []
    
    # 2. Create the CP-SAT model
    model = cp_model.CpModel()

    # 3. Create the variables
    # meet[p1, p2, t, r] is true if p1 and p2 meet at time t in room r.
    meet = {}
    for p1_idx in range(num_people):
        for p2_idx in range(p1_idx + 1, num_people):
            for t_idx in range(num_slots):
                for r_idx in range(num_rooms):
                    meet[p1_idx, p2_idx, t_idx, r_idx] = model.NewBoolVar(
                        f'meet_{p1_idx}_{p2_idx}_{t_idx}_{r_idx}'
                    )

    # 4. Add Constraints
    # Constraint: A person can have at most one meeting per time slot.
    for p_idx in range(num_people):
        for t_idx in range(num_slots):
            meetings_at_t = []
            for r_idx in range(num_rooms):
                # Meetings where p_idx is the first person
                for p2_idx in range(p_idx + 1, num_people):
                    meetings_at_t.append(meet[p_idx, p2_idx, t_idx, r_idx])
                # Meetings where p_idx is the second person
                for p1_idx in range(p_idx):
                    meetings_at_t.append(meet[p1_idx, p_idx, t_idx, r_idx])
            model.AddAtMostOne(meetings_at_t)

    # NEW Constraint: A room can host at most one meeting per time slot.
    for r_idx in range(num_rooms):
        for t_idx in range(num_slots):
            meetings_in_room_at_t = []
            for p1_idx in range(num_people):
                for p2_idx in range(p1_idx + 1, num_people):
                    meetings_in_room_at_t.append(meet[p1_idx, p2_idx, t_idx, r_idx])
            model.AddAtMostOne(meetings_in_room_at_t)

    # Constraint: Do not schedule meetings between blocked pairs.
    for p1_idx, p2_idx in blocked_pairs:
        for t_idx in range(num_slots):
            for r_idx in range(num_rooms):
                model.Add(meet[p1_idx, p2_idx, t_idx, r_idx] == 0)

    # Constraint: A meeting can only happen if both people are available.
    for p1_idx in range(num_people):
        for p2_idx in range(p1_idx + 1, num_people):
            for t_idx in range(num_slots):
                # Check if this time slot index is in both persons' availability list
                if t_idx not in attendees_data[p1_idx]['availability'] or t_idx not in attendees_data[p2_idx]['availability']:
                    for r_idx in range(num_rooms):
                        model.Add(meet[p1_idx, p2_idx, t_idx, r_idx] == 0)

    # 5. Define the Objective Function
    # We want to maximize the total interest score of all scheduled meetings.
    total_interest_score = 0
    for p1_idx in range(num_people):
        for p2_idx in range(p1_idx + 1, num_people):
            score = calculate_interest_score(
                attendees_data[p1_idx],
                attendees_data[p2_idx]
            )
            # Scale score by 10 and convert to integer for the CP-SAT solver, which prefers integers.
            integer_score = int(score * 10)
            if integer_score > 0:
                for t_idx in range(num_slots):
                    for r_idx in range(num_rooms):
                        total_interest_score += meet[p1_idx, p2_idx, t_idx, r_idx] * integer_score
    
    model.Maximize(total_interest_score)

    # 6. Solve the model
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    # 7. Process and return the solution as a list of dictionaries
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        # Create reverse maps to get model objects from solver indices
        people_rev_map = {i: person for person, i in people_map.items()}
        slot_rev_map = {i: slot for slot, i in slot_map.items()}
        room_rev_map = {i: room for room, i in room_map.items()}

        scheduled_meetings = []
        for t_idx in range(num_slots):
            for r_idx in range(num_rooms):
                for p1_idx in range(num_people):
                    for p2_idx in range(p1_idx + 1, num_people):
                        if solver.Value(meet[p1_idx, p2_idx, t_idx, r_idx]) == 1:
                            p1_obj = people_rev_map[p1_idx]
                            p2_obj = people_rev_map[p2_idx]
                            slot_obj = slot_rev_map[t_idx]
                            room_obj = room_rev_map[r_idx]
                            
                            score = calculate_interest_score(
                                attendees_data[p1_idx],
                                attendees_data[p2_idx]
                            )
                            
                            meeting_info = {
                                'attendee1': p1_obj, 'attendee2': p2_obj,
                                'time_slot': slot_obj, 'room': room_obj, 'score': score
                            }
                            scheduled_meetings.append(meeting_info)
        return scheduled_meetings
    else:
        return []