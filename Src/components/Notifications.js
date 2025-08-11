import React, { useState, useEffect } from 'react';
import api from '../api';

const Notifications = () => {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const response = await api.get('/notifications/');
      setNotifications(response.data.results);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, []);

  const markAsRead = async (id) => {
    try {
      await api.post(`/notifications/${id}/mark_as_read/`);
      // Refresh the list to show the change
      fetchNotifications();
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  if (loading) return <p>Loading notifications...</p>;

  return (
    <div>
      <h2>Notifications</h2>
      <ul>
        {notifications.map(note => (
          <li key={note.id} style={{ color: note.is_read ? 'grey' : 'black' }}>
            {note.message} {!note.is_read && <button onClick={() => markAsRead(note.id)} style={{marginLeft: '10px'}}>Mark as Read</button>}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Notifications;