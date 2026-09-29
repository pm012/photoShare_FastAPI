import { useEffect, useState } from 'react';
import api from './api';

const formatDate = (date) => new Intl.DateTimeFormat('uk-UA', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
}).format(new Date(date));

function PublicProfile({ username, onPhotoSelect, onBack }) {
    const [profile, setProfile] = useState(null);
    const [photos, setPhotos] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const loadProfile = async () => {
            try {
                setLoading(true);
                setError('');
                const [profileResponse, photosResponse] = await Promise.all([
                    api.get(`/users/${encodeURIComponent(username)}`),
                    api.get(`/users/${encodeURIComponent(username)}/photos`),
                ]);
                setProfile(profileResponse.data);
                setPhotos(photosResponse.data);
            } catch (err) {
                setError(err.response?.data?.detail || 'Не вдалося завантажити профіль.');
            } finally {
                setLoading(false);
            }
        };
        const request = window.setTimeout(loadProfile, 0);
        return () => window.clearTimeout(request);
    }, [username]);

    if (loading) return <main className="public-profile-page"><div className="feed-status" role="status">Завантажуємо профіль...</div></main>;
    if (error) return <main className="public-profile-page"><button className="back-button" onClick={onBack}>← Назад</button><p className="error-message" role="alert">{error}</p></main>;

    return (
        <main className="public-profile-page">
            <button className="back-button" onClick={onBack}>← Назад до стрічки</button>
            <section className="public-profile-hero">
                <div className="profile-avatar" aria-hidden="true">{profile.username.slice(0, 1).toUpperCase()}</div>
                <div><p className="eyebrow">Community member</p><h2>@{profile.username}</h2><p>На PhotoShare з {formatDate(profile.created_at)}</p></div>
                <div className="public-profile-stat"><strong>{profile.photos_count}</strong><span>Світлин</span></div>
            </section>
            <section className="profile-gallery"><div className="section-heading"><div><p className="eyebrow">Archive</p><h3>Світлини користувача</h3></div><span>{photos.length} у стрічці</span></div>{photos.length === 0 ? <div className="feed-status">У цього користувача ще немає світлин.</div> : <div className="profile-photo-grid">{photos.map((photo) => <article className="profile-photo" key={photo.id} onClick={() => onPhotoSelect(photo.id)} onKeyDown={(event) => event.key === 'Enter' && onPhotoSelect(photo.id)} tabIndex="0" role="button"><img src={photo.url} alt={photo.description || 'Світлина користувача'} /><div><p>{photo.description || 'Без опису'}</p><span>★ {photo.average_rating || '0.0'}</span></div></article>)}</div>}</section>
        </main>
    );
}

export default PublicProfile;
