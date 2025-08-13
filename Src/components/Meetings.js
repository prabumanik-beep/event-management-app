import React, { useEffect } from 'react';
import { useMeetings } from '../hooks/useMeetings';
import { useAuth } from '../context/AuthContext';
import { baseURL } from '../api';
import styles from './Meetings.module.css';
import StatusDisplay from './StatusDisplay';

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
  
  return (
    <div>
      <div className={styles.header}>
        <h2>My Meetings</h2>
        <button onClick={fetchMeetings} disabled={loading}>
          {loading && meetings.length > 0 ? 'Refreshing...' : 'Refresh Meetings'}
        </button>
      </div>

      <StatusDisplay
        loading={loading && meetings.length === 0}
        error={error}
        loadingText="Loading your meetings..."
        emptyText="You have no scheduled meetings."
      >
        <ul>
          {meetings.map((meeting) => (
            <li key={meeting.id} className={styles.meetingItem}>
              <span>
                Meeting with{' '}
                <strong>
                  {userProfile?.username === meeting.attendee1 ? meeting.attendee2 : meeting.attendee1}
                </strong>{' '}
                on {formatDate(meeting.meeting_time)}
              </span>
              <a href={`${baseURL}meetings/${meeting.id}/ical/`} className={styles.calendarButton} download>
                Add to Calendar
              </a>
            </li>
          ))}
        </ul>
      </StatusDisplay>
    </div>
  );
};

export default Meetings;