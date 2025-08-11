import React, { useState, useEffect } from 'react';
import api from '../api';

const Profile = () => {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
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
    // This is a simplified example. A real app would likely need to
    // look up skill IDs based on the names provided.
    console.log("Updating interests (demo)... This requires a more complex UI in a real app.");
    // Example of what a PUT request would look like, though it needs skill IDs.
    // await api.put('/profile/', { interest_ids: [1, 2] });
    // alert("Profile updated!");
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
        <button type="submit" style={{ marginTop: '10px' }}>Update Interests (Demo)</button>
      </form>
    </div>
  );
};

export default Profile;