import { useEffect, useRef, useState } from 'react';
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

const INACTIVITY_TIMEOUT_MS = 20 * 60 * 1000;
const TOKEN_REFRESH_INTERVAL_MS = 5 * 60 * 1000;

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(() => Boolean(localStorage.getItem('token')));
  const [activeView, setActiveView] = useState('feed');
  const [selectedPhotoId, setSelectedPhotoId] = useState(null);
  const [selectedUsername, setSelectedUsername] = useState(null);
  const [currentRole, setCurrentRole] = useState(null);
  const lastRefreshAt = useRef(0);

  useEffect(() => {
    if (!isAuthenticated) return undefined;
    const request = window.setTimeout(async () => {
      try {
        const response = await api.get('/users/me');
        setCurrentRole(normalizeRole(response.data.role));
      } catch {
        localStorage.removeItem('token');
        setIsAuthenticated(false);
        setCurrentRole(null);
      }
    }, 0);
    return () => window.clearTimeout(request);
  }, [isAuthenticated]);

  useEffect(() => {
    if (!isAuthenticated) return undefined;

    let inactivityTimer;
    const refreshToken = async () => {
      if (Date.now() - lastRefreshAt.current < TOKEN_REFRESH_INTERVAL_MS) return;
      try {
        const response = await api.post('/auth/refresh');
        localStorage.setItem('token', response.data.access_token);
        lastRefreshAt.current = Date.now();
      } catch {
        // The response interceptor ends the session when the token is invalid.
      }
    };
    const resetInactivityTimer = () => {
      window.clearTimeout(inactivityTimer);
      inactivityTimer = window.setTimeout(() => {
        localStorage.removeItem('token');
        window.dispatchEvent(new Event('photoshare-auth-expired'));
      }, INACTIVITY_TIMEOUT_MS);
      refreshToken();
    };
    const activityEvents = ['click', 'keydown', 'mousemove', 'scroll', 'touchstart'];

    activityEvents.forEach((eventName) => window.addEventListener(eventName, resetInactivityTimer, { passive: true }));
    resetInactivityTimer();

    return () => {
      window.clearTimeout(inactivityTimer);
      activityEvents.forEach((eventName) => window.removeEventListener(eventName, resetInactivityTimer));
    };
  }, [isAuthenticated]);

  useEffect(() => {
    const handleAuthExpired = () => {
      setIsAuthenticated(false);
      setActiveView('feed');
      setSelectedPhotoId(null);
      setSelectedUsername(null);
      setCurrentRole(null);
      lastRefreshAt.current = 0;
    };

    window.addEventListener('photoshare-auth-expired', handleAuthExpired);
    return () => window.removeEventListener('photoshare-auth-expired', handleAuthExpired);
  }, []);

  const handleLoginSuccess = () => {
    setActiveView('feed');
    setSelectedPhotoId(null);
    setSelectedUsername(null);
    setCurrentRole(null);
    lastRefreshAt.current = 0;
    setIsAuthenticated(true);
  };

  const handleLogout = async () => {
    try {
      await api.post('/auth/logout');
    } catch {
      // Локальну сесію все одно потрібно завершити, якщо API недоступний.
    } finally {
      localStorage.removeItem('token');
      setIsAuthenticated(false);
      setActiveView('feed');
      setSelectedPhotoId(null);
      setSelectedUsername(null);
      setCurrentRole(null);
      lastRefreshAt.current = 0;
    }
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
