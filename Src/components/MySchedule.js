import React, { useState, useEffect } from 'react';
import api from '../api'; // Import our configured API service

const MySchedule = () => {
  const [meetings, setMeetings] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMeetings = async () => {
      try {
        // The auth header and token refreshing are handled automatically!
        const response = await api.get('/meetings/');
        setMeetings(response.data.results);
      } catch (error) {
        console.error('Failed to fetch meetings:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchMeetings();
  }, []);

  if (loading) return <p>Loading your schedule...</p>;

  return (
    <div>
      <h2>My Meetings</h2>
      <ul>
        {meetings.map((meeting) => (
          <li key={meeting.id}>
            Meeting with {meeting.other_attendee.username} at {new Date(meeting.time_slot.start_time).toLocaleString()}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default MySchedule;