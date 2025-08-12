import React, { useState, useEffect } from 'react';
import api from '../api';

const Profile = () => {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isUpdating, setIsUpdating] = useState(false);
  const [interests, setInterests] = useState('');
  const [message, setMessage] = useState({ text: '', type: '' }); // For success/error messages

  const fetchProfile = async () => {
    try {
      const response = await api.get('/profile/');
      setProfile(response.data);
      // Pre-fill the interest input with existing interests
      setInterests(response.data.interests.map(i => i.name).join(', '));
    } catch (error) {
      console.error('Failed to fetch profile:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, []);

  const handleUpdate = async (e) => {
    e.preventDefault();
    setIsUpdating(true);
    setMessage({ text: '', type: '' }); // Clear previous messages
    try {
      // Split the comma-separated string into an array of trimmed, non-empty strings.
      const interestNames = interests.split(',').map(name => name.trim()).filter(name => name);
      
      // The backend is already configured to handle this payload.
      const response = await api.put('/profile/', { interest_names: interestNames });
      setMessage({ text: 'Profile updated successfully!', type: 'success' });
      // OPTIMIZATION: Use the data returned from the PUT request directly.
      setProfile(response.data);
      // Also update the input field to reflect the canonical names from the server
      setInterests(response.data.interests.map(i => i.name).join(', '));
    } catch (error) {
      console.error('Failed to update profile:', error);
      setMessage({ text: 'Failed to update profile.', type: 'error' });
    } finally {
      setIsUpdating(false);
    }
  };

  if (loading) return <p>Loading profile...</p>;
  if (!profile) return <p>Could not load profile.</p>;

  return (
    <div>
      <h2>My Profile</h2>
      <p><strong>Username:</strong> {profile.username}</p>
      <p><strong>Role:</strong> {profile.role}</p>
      <form onSubmit={handleUpdate}>
        <label>
          Interests (comma-separated):
          <input 
            type="text" 
            value={interests}
            onChange={(e) => setInterests(e.target.value)}
            style={{ width: '300px', marginLeft: '10px' }}
          />
        </label>
        <br />
        {message.text && <p style={{ color: message.type === 'error' ? 'red' : 'green' }}>{message.text}</p>}
        <button type="submit" style={{ marginTop: '10px' }} disabled={isUpdating}>
          {isUpdating ? 'Updating...' : 'Update Interests'}
        </button>
      </form>
    </div>
  );
};

export default Profile;