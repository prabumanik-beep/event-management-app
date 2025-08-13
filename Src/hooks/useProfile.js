import { useState, useEffect, useCallback } from 'react';
import api from '../api';

export const useProfile = () => {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isUpdating, setIsUpdating] = useState(false);
  const [message, setMessage] = useState({ text: '', type: '' });

  const fetchProfile = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get('/profile/');
      setError(null); // Clear previous errors on success
      setProfile(response.data);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch profile:', error);
      setError('Could not load profile. Please try refreshing the page.');
      return null; // Return null on failure
    } finally {
      setLoading(false);
    }
  }, []);

  const updateProfileInterests = useCallback(async (interestNames) => {
    setIsUpdating(true);
    setMessage({ text: '', type: '' });
    try {
      const response = await api.put('/profile/', { interest_names: interestNames });
      setProfile(response.data);
      setMessage({ text: 'Profile updated successfully!', type: 'success' });
      return response.data;
    } catch (error) {
      console.error('Failed to update profile:', error);
      setMessage({ text: 'Failed to update profile.', type: 'error' });
      return null;
    } finally {
      setIsUpdating(false);
    }
  }, []);

  return { profile, loading, error, isUpdating, message, fetchProfile, updateProfileInterests };
};