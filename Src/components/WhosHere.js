import React, { useState, useEffect } from 'react';
import api from '../api';

const WhosHere = () => {
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchProfiles = async () => {
      try {
        const response = await api.get('/public-profiles/');
        setProfiles(response.data.results);
      } catch (error) {
        console.error("Failed to fetch who's here list:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchProfiles();
  }, []);

  if (loading) return <p>Loading checked-in attendees...</p>;

  return (
    <div>
      <h2>Who's Here</h2>
      <ul>
        {profiles.map(profile => (
          <li key={profile.id}>{profile.username} - Interests: {profile.interests.map(i => i.name).join(', ')}</li>
        ))}
      </ul>
    </div>
  );
};

export default WhosHere;