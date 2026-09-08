import { useEffect, useState } from 'react';
import api from './api';

const formatDate = (date) => new Intl.DateTimeFormat('uk-UA', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
}).format(new Date(date));

function Profile() {
    const [user, setUser] = useState(null);
    const [photos, setPhotos] = useState([]);
    const [username, setUsername] = useState('');
    const [isEditing, setIsEditing] = useState(false);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');
    const [saveMessage, setSaveMessage] = useState('');

    const loadProfile = async () => {
        try {
            setLoading(true);
            setError('');
            const profileResponse = await api.get('/users/me');
            const profile = profileResponse.data;
            const photosResponse = await api.get('/search/photos', {
                params: { sort_by: 'date', order: 'desc' },
            });
            setUser(profile);
            setUsername(profile.username);
            setPhotos(photosResponse.data.filter((photo) => photo.user_id === profile.id));
        } catch (err) {
            setError(err.response?.data?.detail || 'Не вдалося завантажити профіль.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        const request = window.setTimeout(loadProfile, 0);
        return () => window.clearTimeout(request);
    }, []);

    const handleSaveUsername = async (event) => {
        event.preventDefault();
        const nextUsername = username.trim();
        if (!nextUsername) {
            setError('Username не може бути порожнім.');
            return;
        }

        try {
            setSaving(true);
            setError('');
            setSaveMessage('');
            const response = await api.put('/users/me', { username: nextUsername });
            setUser(response.data);
            setUsername(response.data.username);
            setIsEditing(false);
            setSaveMessage('Username успішно оновлено.');
        } catch (err) {
            setError(err.response?.data?.detail || 'Не вдалося оновити username.');
        } finally {
            setSaving(false);
        }
    };

    if (loading) return <main className="profile-page"><div className="feed-status" role="status">Завантажуємо профіль...</div></main>;
    if (error && !user) return <main className="profile-page"><p className="error-message" role="alert">{error}</p></main>;

    return (
        <main className="profile-page">
            <section className="profile-hero">
                <div className="profile-avatar" aria-hidden="true">{user.username.slice(0, 1).toUpperCase()}</div>
                <div className="profile-intro">
                    <p className="eyebrow">Your space</p>
                    {isEditing ? (
                        <form className="username-form" onSubmit={handleSaveUsername}>
                            <label htmlFor="profile-username">Username</label>
                            <div><input id="profile-username" value={username} onChange={(event) => setUsername(event.target.value)} autoFocus /><button className="primary-button" disabled={saving}>{saving ? 'Зберігаємо...' : 'Зберегти'}</button></div>
                        </form>
                    ) : (
                        <div className="profile-title-row"><h2>@{user.username}</h2><button className="secondary-button" onClick={() => { setIsEditing(true); setSaveMessage(''); }}>Редагувати</button></div>
                    )}
                    <p className="profile-email">{user.email}</p>
                </div>
                <div className="profile-status"><span className={user.is_active ? 'status-dot active' : 'status-dot'}></span>{user.is_active ? 'Активний акаунт' : 'Акаунт неактивний'}</div>
            </section>

            {error && <p className="error-message" role="alert">{error}</p>}
            {saveMessage && <p className="success-message" role="status">{saveMessage}</p>}

            <section className="profile-stats" aria-label="Статистика профілю">
                <div><strong>{photos.length}</strong><span>Світлин</span></div>
                <div><strong>{user.role}</strong><span>Роль</span></div>
                <div><strong>{formatDate(user.created_at)}</strong><span>На PhotoShare з</span></div>
            </section>

            <section className="profile-gallery">
                <div className="section-heading"><div><p className="eyebrow">Archive</p><h3>Мої світлини</h3></div><span>{photos.length} {photos.length === 1 ? 'світлина' : 'світлин'}</span></div>
                {photos.length === 0 ? <div className="feed-status">У вас ще немає завантажених світлин.</div> : <div className="profile-photo-grid">{photos.map((photo) => <article className="profile-photo" key={photo.id}><img src={photo.url} alt={photo.description || 'Моя світлина'} /><div><p>{photo.description || 'Без опису'}</p><span>★ {photo.average_rating || '0.0'}</span></div></article>)}</div>}
            </section>
        </main>
    );
}

export default Profile;
