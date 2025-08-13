import React, { useEffect } from 'react';
import { useMeetings } from '../hooks/useMeetings';
import { useAuth } from '../context/AuthContext';
import styles from './Meetings.module.css';

const formatDate = (dateString) => {
  const options = {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  };
  return new Date(dateString).toLocaleString(undefined, options);
};

const Meetings = () => {
  const { meetings, loading, error, fetchMeetings } = useMeetings();
  const { userProfile } = useAuth();

  useEffect(() => {
    fetchMeetings();
  }, [fetchMeetings]);

  // Show a full-page loader only on the initial fetch
  if (loading && meetings.length === 0) return <p>Loading meetings...</p>;
  if (error) return <p style={{ color: 'red' }}>{error}</p>;

  return (
    <div>
      <div className={styles.header}>
        <h2>My Meetings</h2>
        <button onClick={fetchMeetings} disabled={loading}>
          {loading ? 'Refreshing...' : 'Refresh Meetings'}
        </button>
      </div>

      {meetings.length === 0 && !loading ? (
        <p>You have no scheduled meetings.</p>
      ) : (
        <ul>
          {meetings.map((meeting) => (
            <li key={meeting.id}>
              Meeting with{' '}
              <strong>
                {userProfile?.username === meeting.attendee1 ? meeting.attendee2 : meeting.attendee1}
              </strong>{' '}
              on {formatDate(meeting.time_slot)}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default Meetings;