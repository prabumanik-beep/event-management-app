import React, { useEffect } from 'react';
import { useMeetings } from '../hooks/useMeetings';

const Meetings = () => {
  const { meetings, loading, error, fetchMeetings } = useMeetings();

  useEffect(() => {
    fetchMeetings();
  }, [fetchMeetings]);

  if (loading) return <p>Loading meetings...</p>;
  if (error) return <p style={{ color: 'red' }}>{error}</p>;

  return (
    <div>
      <h2>My Meetings</h2>
      {meetings.length === 0 ? (
        <p>You have no scheduled meetings.</p>
      ) : (
        <ul>
          {meetings.map((meeting) => (
            <li key={meeting.id}>
              Meeting with <strong>{meeting.user1}</strong> and <strong>{meeting.user2}</strong> on{' '}
              {new Date(meeting.meeting_time).toLocaleString()}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default Meetings;