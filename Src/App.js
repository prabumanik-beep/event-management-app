import React, { useState } from 'react';
import Login from './components/Login';
import MySchedule from './components/MySchedule';
import Profile from './components/Profile';
import WhosHere from './components/WhosHere';
import Notifications from './components/Notifications';

function App() {
  // A simple way to check if the user is logged in by seeing if a token exists.
  const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem('access_token'));
  // State to manage which view is currently active
  const [activeView, setActiveView] = useState('schedule');
  
  const handleLoginSuccess = () => {
    setIsLoggedIn(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setIsLoggedIn(false);
  };

  const renderActiveView = () => {
    switch (activeView) {
      case 'profile':
        return <Profile />;
      case 'whos-here':
        return <WhosHere />;
      case 'notifications':
        return <Notifications />;
      case 'schedule':
      default:
        return <MySchedule />;
    }
  };

  return (
    <div className="App">
      <header>
        <h1>Vibe Coding Event</h1>
        {isLoggedIn && <button onClick={handleLogout}>Logout</button>}
      </header>
      {isLoggedIn && (
        <nav>
          <button onClick={() => setActiveView('schedule')}>My Schedule</button>
          <button onClick={() => setActiveView('profile')}>My Profile</button>
          <button onClick={() => setActiveView('whos-here')}>Who's Here</button>
          <button onClick={() => setActiveView('notifications')}>Notifications</button>
        </nav>
      )}
      <main>
        {isLoggedIn ? renderActiveView() : <Login onLoginSuccess={handleLoginSuccess} />}
      </main>
    </div>
  );
}

export default App;