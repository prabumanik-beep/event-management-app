import React, { useState, useEffect } from 'react';
import api from '../api';

const Profile = () => {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isUpdating, setIsUpdating] = useState(false);
  const [interests, setInterests] = useState('');

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
    try {
      // Split the comma-separated string into an array of trimmed, non-empty strings.
      const interestNames = interests.split(',').map(name => name.trim()).filter(name => name);
      
      // The backend is already configured to handle this payload.
      await api.put('/profile/', { interest_names: interestNames });
      alert("Profile updated successfully!");
      // Re-fetch the profile to display the updated interests immediately.
      fetchProfile();
    } catch (error) {
      console.error('Failed to update profile:', error);
      alert("Failed to update profile.");
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
        <button type="submit" style={{ marginTop: '10px' }} disabled={isUpdating}>
          {isUpdating ? 'Updating...' : 'Update Interests'}
        </button>
      </form>
    </div>
  );
};

export default Profile;