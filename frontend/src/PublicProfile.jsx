import { useEffect, useState } from 'react';
import api from './api';
import ProfilePhotoGrid from './ProfilePhotoGrid';
import UserAvatar from './UserAvatar';
import './Profile.css';

const formatDate = (date) => new Intl.DateTimeFormat('en-US', {
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
                setError(err.response?.data?.detail || 'Could not load the profile.');
            } finally {
                setLoading(false);
            }
        };
        const request = window.setTimeout(loadProfile, 0);
        return () => window.clearTimeout(request);
    }, [username]);

    const backButton = <button className="btn btn-secondary pr-back" type="button" onClick={onBack}>← Back</button>;

    if (loading) return <main className="public-profile-page"><div className="feed-status" role="status">Loading profile...</div></main>;
    if (error) return <main className="public-profile-page">{backButton}<p className="error-message" role="alert">{error}</p></main>;

    return (
        <main className="public-profile-page">
            {backButton}
            <section className="pr-hero">
                <UserAvatar username={profile.username} url={profile.avatar_url} size={120} />
                <div className="pr-intro">
                    <div className="pr-name-row"><h2>@{profile.username}</h2></div>
                    <p className="pr-muted">Member since {formatDate(profile.created_at)}</p>
                </div>
                <div className="pr-stat"><strong>{profile.photos_count}</strong><span>{profile.photos_count === 1 ? 'Photo' : 'Photos'}</span></div>
            </section>

            <section style={{ marginTop: 32 }}>
                <div className="pr-section-header"><h3>Photos</h3><span>{photos.length} {photos.length === 1 ? 'photo' : 'photos'}</span></div>
                {photos.length === 0 ? <div className="feed-status">This user hasn't uploaded any photos yet.</div> : <ProfilePhotoGrid photos={photos} onSelect={onPhotoSelect} />}
            </section>
        </main>
    );
}

export default PublicProfile;
