import React, { useState, useEffect } from 'react';
import Login from './Login';
import PhotoFeed from './PhotoFeed'; // Added photo feed

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      setIsAuthenticated(true);
    }
  }, []);

  const handleLoginSuccess = () => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsAuthenticated(false);
  };

  return (
    <div>
      {isAuthenticated ? (
        <div>
          {/* Верхня панель (Header) */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 40px', backgroundColor: '#f8f9fa', borderBottom: '1px solid #ddd' }}>
            <h1 style={{ margin: 0, fontSize: '24px' }}>PhotoShare</h1>
            <button onClick={handleLogout} style={{ padding: '8px 15px', backgroundColor: '#dc3545', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
              Вийти (Logout)
            </button>
          </div>
          
          {/* Mount photo feed */}
          <PhotoFeed />
        </div>
      ) : (
        <Login onLoginSuccess={handleLoginSuccess} />
      )}
    </div>
  );
}

export default App;
