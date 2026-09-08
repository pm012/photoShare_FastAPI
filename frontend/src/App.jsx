import { useEffect, useState } from 'react';
import Login from './Login';
import PhotoFeed from './PhotoFeed';
import Profile from './Profile';
import PhotoPage from './PhotoPage';
import AdminPanel from './AdminPanel';
import api from './api';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(() => Boolean(localStorage.getItem('token')));
  const [activeView, setActiveView] = useState('feed');
  const [selectedPhotoId, setSelectedPhotoId] = useState(null);
  const [currentRole, setCurrentRole] = useState(null);

  useEffect(() => {
    if (!isAuthenticated) return undefined;
    const request = window.setTimeout(async () => {
      try {
        const response = await api.get('/users/me');
        setCurrentRole(String(response.data.role).toLowerCase().replace('userrole.', ''));
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
            <button className="brand-button" onClick={() => { setSelectedPhotoId(null); setActiveView('feed'); }}>PhotoShare</button>
            <nav className="main-nav" aria-label="Основна навігація">
              <button className={activeView === 'feed' ? 'nav-button active' : 'nav-button'} onClick={() => { setSelectedPhotoId(null); setActiveView('feed'); }}>Стрічка</button>
              <button className={activeView === 'profile' ? 'nav-button active' : 'nav-button'} onClick={() => setActiveView('profile')}>Профіль</button>
              {['admin', 'moderator'].includes(currentRole) && <button className={activeView === 'admin' ? 'nav-button active' : 'nav-button'} onClick={() => setActiveView('admin')}>Керування</button>}
            </nav>
            <button className="logout-button" onClick={handleLogout}>Вийти</button>
          </div>
          {selectedPhotoId ? <PhotoPage photoId={selectedPhotoId} onBack={() => setSelectedPhotoId(null)} /> : activeView === 'feed' ? <PhotoFeed onPhotoSelect={setSelectedPhotoId} /> : activeView === 'profile' ? <Profile /> : <AdminPanel currentRole={currentRole} />}
        </div>
      ) : (
        <Login onLoginSuccess={handleLoginSuccess} />
      )}
    </div>
  );
}

export default App;
