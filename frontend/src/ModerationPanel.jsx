import { useEffect, useState } from 'react';
import api from './api';

const getError = (error) => error.response?.data?.detail || 'Could not complete the moderation action.';

function ModerationPanel() {
    const [query, setQuery] = useState('');
    const [users, setUsers] = useState([]);
    const [photos, setPhotos] = useState([]);
    const [selectedUserId, setSelectedUserId] = useState('');
    const [selectedPhotoId, setSelectedPhotoId] = useState('');
    const [ratings, setRatings] = useState([]);
    const [loading, setLoading] = useState(false);
    const [ratingsLoading, setRatingsLoading] = useState(false);
    const [deletingId, setDeletingId] = useState(null);
    const [error, setError] = useState('');
    const [message, setMessage] = useState('');

    useEffect(() => {
        const loadInitialUsers = async () => {
            try {
                const response = await api.get('/search/users', { params: { page: 1, page_size: 20 } });
                setUsers(response.data);
            } catch (err) {
                setError(getError(err));
            }
        };
        loadInitialUsers();
    }, []);

    const searchUsers = async (event) => {
        event.preventDefault();
        try {
            setLoading(true);
            setError('');
            setMessage('');
            const response = await api.get('/search/users', { params: { query: query.trim() || undefined, page: 1, page_size: 20 } });
            setUsers(response.data);
            setSelectedUserId('');
            setPhotos([]);
            setSelectedPhotoId('');
            setRatings([]);
        } catch (err) {
            setError(getError(err));
        } finally {
            setLoading(false);
        }
    };

    const loadPhotos = async (userId) => {
        setSelectedUserId(userId);
        setSelectedPhotoId('');
        setRatings([]);
        if (!userId) {
            setPhotos([]);
            return;
        }
        try {
            setLoading(true);
            setError('');
            const response = await api.get('/search/photos', { params: { user_id: userId, sort_by: 'date', order: 'desc' } });
            setPhotos(response.data);
        } catch (err) {
            setError(getError(err));
        } finally {
            setLoading(false);
        }
    };

    const loadRatings = async (photoId) => {
        setSelectedPhotoId(photoId);
        if (!photoId) {
            setRatings([]);
            return;
        }
        try {
            setRatingsLoading(true);
            setError('');
            const response = await api.get(`/photos/${photoId}/ratings`);
            setRatings(response.data);
        } catch (err) {
            setError(getError(err));
        } finally {
            setRatingsLoading(false);
        }
    };

    const deleteRating = async (ratingId) => {
        if (!window.confirm('Delete this rating?')) return;
        try {
            setDeletingId(ratingId);
            setError('');
            await api.delete(`/photos/rate/${ratingId}`);
            setRatings((items) => items.filter((rating) => rating.id !== ratingId));
            setMessage('Rating deleted.');
        } catch (err) {
            setError(getError(err));
        } finally {
            setDeletingId(null);
        }
    };

    const selectedPhoto = photos.find((photo) => String(photo.id) === String(selectedPhotoId));

    return (
        <main className="moderation-page">
            <header className="admin-heading"><div><p className="eyebrow">Moderation desk</p><h2>Content moderation</h2><p>Browse users' photos and manage community ratings.</p></div><span className="role-badge">Moderator tools</span></header>
            <form className="admin-search" onSubmit={searchUsers}><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Find a creator by username or email" aria-label="Search creators" /><button className="primary-button" disabled={loading}>{loading ? 'Searching...' : 'Find creator'}</button></form>
            {error && <p className="error-message" role="alert">{error}</p>}
            {message && <p className="success-message" role="status">{message}</p>}
            <section className="moderation-filters"><label><span>Creator</span><select value={selectedUserId} onChange={(event) => loadPhotos(event.target.value)}><option value="">Select a user</option>{users.map((user) => <option value={user.id} key={user.id}>@{user.username} · {user.email}</option>)}</select></label><label><span>Photo</span><select value={selectedPhotoId} onChange={(event) => loadRatings(event.target.value)} disabled={!selectedUserId || loading}><option value="">Select a photo</option>{photos.map((photo) => <option value={photo.id} key={photo.id}>#{photo.id} · {photo.description || 'No description'}</option>)}</select></label></section>
            {selectedPhoto && <section className="moderation-photo"><img src={selectedPhoto.url} alt={selectedPhoto.description || 'Photo under moderation'} /><div><p className="eyebrow">Selected photo</p><h3>{selectedPhoto.description || 'Photo without a description'}</h3><span>Average rating: {selectedPhoto.average_rating?.toFixed(1) || '0.0'}</span></div></section>}
            <section className="ratings-section"><div className="section-heading"><div><p className="eyebrow">Ratings</p><h3>Photo ratings</h3></div><span>{ratings.length} ratings</span></div>{!selectedPhotoId ? <div className="feed-status">Select a creator and photo to view ratings.</div> : ratingsLoading ? <div className="feed-status" role="status">Loading ratings...</div> : ratings.length === 0 ? <div className="feed-status">This photo has no ratings.</div> : <div className="rating-list">{ratings.map((rating) => <article className="rating-row" key={rating.id}><div><strong>Rating {rating.rate}/5</strong><small>User #{rating.user_id}</small></div><button className="danger-button" onClick={() => deleteRating(rating.id)} disabled={deletingId === rating.id}>{deletingId === rating.id ? 'Deleting...' : 'Delete'}</button></article>)}</div>}</section>
        </main>
    );
}

export default ModerationPanel;
