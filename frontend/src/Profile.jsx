import { useEffect, useState } from 'react';
import api from './api';
import { AvatarUpload } from './AvatarUpload'; // Interactive avatar uploader
import ProfilePhotoGrid from './ProfilePhotoGrid';
import './Profile.css';

const formatDate = (date) => new Intl.DateTimeFormat('en-US', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
}).format(new Date(date));

// "UserRole.ADMIN" / "admin" -> "Admin"
const roleLabel = (role) => {
    const value = String(role || '').toLowerCase();
    const name = value.includes('.') ? value.split('.').pop() : value;
    return name.charAt(0).toUpperCase() + name.slice(1);
};

function Profile({ onPhotoSelect }) {
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
            // The user's own photos come from the public-photos endpoint, so they are not
            // limited to the first page of the global feed.
            const photosResponse = await api.get(`/users/${encodeURIComponent(profile.username)}/photos`);
            setUser(profile);
            setUsername(profile.username);
            setPhotos(photosResponse.data);
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to load the profile.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        const request = window.setTimeout(loadProfile, 0);
        return () => window.clearTimeout(request);
    }, []);

    // Success messages disappear on their own.
    useEffect(() => {
        if (!saveMessage) return undefined;
        const timer = window.setTimeout(() => setSaveMessage(''), 4000);
        return () => window.clearTimeout(timer);
    }, [saveMessage]);

    const handleSaveUsername = async (event) => {
        event.preventDefault();
        const nextUsername = username.trim();
        if (!nextUsername) {
            setError('Username cannot be empty.');
            return;
        }
        if (nextUsername === user.username) {
            setIsEditing(false);
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
            setSaveMessage('Username updated.');
        } catch (err) {
            const detail = err.response?.data?.detail;
            setError(Array.isArray(detail) ? detail.map((item) => item.msg).join(', ') : detail || 'Could not update the username.');
        } finally {
            setSaving(false);
        }
    };

    const handleCancelEdit = () => {
        setUsername(user.username);
        setError('');
        setIsEditing(false);
    };

    // Update the avatar link in the profile state after it was uploaded to Cloudinary.
    const handleAvatarUpdated = (newUrl) => {
        setUser((prevUser) => ({ ...prevUser, avatar_url: newUrl }));
        setSaveMessage(newUrl ? 'Avatar updated.' : 'Avatar removed.');
    };

    if (loading) return <main className="profile-page"><div className="feed-status" role="status">Loading profile...</div></main>;
    if (error && !user) return <main className="profile-page"><p className="error-message" role="alert">{error}</p></main>;

    return (
        <main className="profile-page">
            <section className="pr-hero">
                <AvatarUpload
                    currentAvatarUrl={user.avatar_url}
                    userName={user.username}
                    onAvatarUpdated={handleAvatarUpdated}
                />

                <div className="pr-intro">
                    {isEditing ? (
                        <form className="pr-username-form" onSubmit={handleSaveUsername}>
                            <label className="pr-label" htmlFor="profile-username">Username</label>
                            <div className="pr-username-form__row">
                                <input id="profile-username" className="field" type="text" value={username} onChange={(event) => setUsername(event.target.value)} minLength={3} maxLength={50} autoComplete="off" autoFocus />
                                <button className="btn btn-primary" type="submit" disabled={saving}>{saving ? 'Saving...' : 'Save'}</button>
                                <button className="btn btn-secondary" type="button" onClick={handleCancelEdit} disabled={saving}>Cancel</button>
                            </div>
                        </form>
                    ) : (
                        <div className="pr-name-row">
                            <h2>@{user.username}</h2>
                            <button className="btn btn-secondary" type="button" onClick={() => { setIsEditing(true); setSaveMessage(''); }}>Edit</button>
                        </div>
                    )}
                    <p className="pr-muted">{user.email}</p>
                </div>

                <span className={user.is_active ? 'pr-badge is-active' : 'pr-badge'}>
                    <span className="pr-badge__dot" aria-hidden="true"></span>
                    {user.is_active ? 'Active account' : 'Inactive account'}
                </span>
            </section>

            {error && <p className="error-message" role="alert" style={{ marginTop: 20 }}>{error}</p>}
            {saveMessage && <p className="success-message" role="status" style={{ marginTop: 20 }}>{saveMessage}</p>}

            <section className="pr-stats" aria-label="Profile statistics">
                <div className="pr-stat"><strong>{photos.length}</strong><span>Photos</span></div>
                <div className="pr-stat"><strong>{roleLabel(user.role)}</strong><span>Role</span></div>
                <div className="pr-stat"><strong>{formatDate(user.created_at)}</strong><span>Member since</span></div>
            </section>

            <section>
                <div className="pr-section-header"><h3>My photos</h3><span>{photos.length} {photos.length === 1 ? 'photo' : 'photos'}</span></div>
                {photos.length === 0 ? <div className="feed-status">You haven't uploaded any photos yet.</div> : <ProfilePhotoGrid photos={photos} onSelect={onPhotoSelect} />}
            </section>
        </main>
    );
}

export default Profile;