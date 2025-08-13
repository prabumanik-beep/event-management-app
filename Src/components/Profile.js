import React, { useState, useEffect } from 'react';
import { useProfile } from '../hooks/useProfile';
import profileStyles from './Profile.module.css';
import formStyles from './Form.module.css';
import Spinner from './Spinner';
import StatusDisplay from './StatusDisplay';

const Profile = () => {
  const { profile, loading, error, isUpdating, message, fetchProfile, updateProfileInterests } = useProfile();
  const [interests, setInterests] = useState('');

  useEffect(() => {
    const loadProfile = async () => {
      const initialProfile = await fetchProfile();
      if (initialProfile) {
        setInterests(initialProfile.interests.map(i => i.name).join(', '));
      }
    };
    loadProfile();
  }, [fetchProfile]);

  const handleUpdate = async (e) => {
    e.preventDefault();
    const interestNames = interests.split(',').map(name => name.trim()).filter(name => name);
    const updatedProfile = await updateProfileInterests(interestNames);
    if (updatedProfile) {
      setInterests(updatedProfile.interests.map(i => i.name).join(', '));
    }
  };

  return (
    <StatusDisplay loading={loading} error={error} loadingText="Loading profile..." emptyText="Profile not found.">
      {profile && (
        <div className={profileStyles.profileContainer}>
          <div className={profileStyles.profileCard}>
            <h2>My Profile</h2>
            <p><strong>Username:</strong> {profile.username}</p>
            <p><strong>Role:</strong> {profile.role}</p>
            <form onSubmit={handleUpdate} className={profileStyles.profileForm}>
              <div className={formStyles.inputGroup}>
                <label htmlFor="profile-interests">Interests (comma-separated):</label>
                <input
                  id="profile-interests"
                  type="text"
                  value={interests}
                  onChange={(e) => setInterests(e.target.value)}
                  disabled={isUpdating}
                />
              </div>
              {message.text && <p className={`${formStyles.formMessage} ${formStyles[message.type]}`}>{message.text}</p>}
              <button type="submit" disabled={isUpdating} className={profileStyles.updateButton}>
                {isUpdating ? <Spinner /> : 'Update Interests'}
              </button>
            </form>
          </div>
        </div>
      )}
    </StatusDisplay>
  );
};

export default Profile;