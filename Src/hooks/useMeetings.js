import { useState, useCallback } from 'react';
import api from '../api';

export const useMeetings = () => {
  const [meetings, setMeetings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchMeetings = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get('/meetings/');
      setMeetings(response.data);
    } catch (err) {
      setError('Failed to load meetings.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  return { meetings, loading, error, fetchMeetings };
};