import { useEffect, useState } from 'react';
import Login from './Login';
import PhotoFeed from './PhotoFeed';
import Profile from './Profile';
import PhotoPage from './PhotoPage';
import AdminPanel from './AdminPanel';
import ModerationPanel from './ModerationPanel';
import PublicProfile from './PublicProfile';
import api from './api';

const normalizeRole = (role) => {
  const value = String(role || '').toLowerCase();
  return value.includes('.') ? value.split('.').pop() : value;
};

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(() => Boolean(localStorage.getItem('token')));
  const [activeView, setActiveView] = useState('feed');
  const [selectedPhotoId, setSelectedPhotoId] = useState(null);
  const [selectedUsername, setSelectedUsername] = useState(null);
  const [currentRole, setCurrentRole] = useState(null);

  useEffect(() => {
    if (!isAuthenticated) return undefined;
    const request = window.setTimeout(async () => {
      try {
        const response = await api.get('/users/me');
        setCurrentRole(normalizeRole(response.data.role));
      } catch {
        setCurrentRole(null);
      }
    }, 0);
    return () => window.clearTimeout(request);
  }, [isAuthenticated]);

  const handleLoginSuccess = () => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsAuthenticated(false);
    setActiveView('feed');
    setCurrentRole(null);
  };

  return (
    <div>
      {isAuthenticated ? (
        <div>
          <div className="app-header">
            <button className="brand-button" onClick={() => { setSelectedPhotoId(null); setSelectedUsername(null); setActiveView('feed'); }}>PhotoShare</button>
            <nav className="main-nav" aria-label="Основна навігація">
              <button className={activeView === 'feed' ? 'nav-button active' : 'nav-button'} onClick={() => { setSelectedPhotoId(null); setSelectedUsername(null); setActiveView('feed'); }}>Стрічка</button>
              <button className={activeView === 'profile' ? 'nav-button active' : 'nav-button'} onClick={() => setActiveView('profile')}>Профіль</button>
              {['admin', 'moderator'].includes(currentRole) && <button className={activeView === 'admin' ? 'nav-button active' : 'nav-button'} onClick={() => setActiveView('admin')}>Керування</button>}
              {['admin', 'moderator'].includes(currentRole) && <button className={activeView === 'moderation' ? 'nav-button active' : 'nav-button'} onClick={() => setActiveView('moderation')}>Модерація</button>}
            </nav>
            <button className="logout-button" onClick={handleLogout}>Вийти</button>
          </div>
          {selectedPhotoId ? <PhotoPage photoId={selectedPhotoId} onBack={() => setSelectedPhotoId(null)} /> : selectedUsername ? <PublicProfile username={selectedUsername} onPhotoSelect={setSelectedPhotoId} onBack={() => setSelectedUsername(null)} /> : activeView === 'feed' ? <PhotoFeed onPhotoSelect={setSelectedPhotoId} onProfileSelect={setSelectedUsername} /> : activeView === 'profile' ? <Profile /> : activeView === 'admin' ? <AdminPanel currentRole={currentRole} /> : <ModerationPanel />}
        </div>
      ) : (
        <Login onLoginSuccess={handleLoginSuccess} />
      )}
    </div>
  );
}

export default App;
