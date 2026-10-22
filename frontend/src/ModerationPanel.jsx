import { useEffect, useState } from 'react';
import api from './api';
import UserAvatar from './UserAvatar';
import useDebouncedValue from './useDebouncedValue';
import './ModerationPanel.css';

const PAGE_SIZE = 20;

const SORTS = [
    { value: 'date-desc', label: 'Newest first', sortBy: 'date', order: 'desc' },
    { value: 'date-asc', label: 'Oldest first', sortBy: 'date', order: 'asc' },
    { value: 'rating-desc', label: 'Highest rated', sortBy: 'rating', order: 'desc' },
    { value: 'rating-asc', label: 'Lowest rated', sortBy: 'rating', order: 'asc' },
];
const DEFAULT_FILTERS = { creator: null, keyword: '', sort: 'date-desc', page: 1 };

// Remembers the filters while the moderator opens a photo page and comes back.
let savedFilters = null;

const getError = (error, fallback = 'Could not complete the moderation action.') => {
    const detail = error.response?.data?.detail;
    return Array.isArray(detail) ? detail.map((item) => item.msg).join(', ') : detail || fallback;
};
const formatDate = (date) => new Date(date).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });

// Type a username or email, pick a user from the suggestions.
function CreatorPicker({ creator, onSelect, onClear }) {
    const [text, setText] = useState('');
    const [open, setOpen] = useState(false);
    const [results, setResults] = useState([]);
    const [searching, setSearching] = useState(false);
    const typed = text.trim();
    const debounced = useDebouncedValue(typed, 300);

    useEffect(() => {
        if (!debounced) return undefined;
        let ignore = false;
        const request = window.setTimeout(async () => {
            setSearching(true);
            try {
                const response = await api.get('/search/users', { params: { query: debounced, page: 1, page_size: 8 } });
                if (!ignore) setResults(response.data);
            } catch {
                if (!ignore) setResults([]);
            } finally {
                if (!ignore) setSearching(false);
            }
        }, 0);
        return () => {
            ignore = true;
            window.clearTimeout(request);
        };
    }, [debounced]);

    if (creator) {
        return (
            <div className="mo-chip">
                <UserAvatar username={creator.username} url={creator.avatar_url} size={26} />
                <span className="mo-chip__name">@{creator.username}</span>
                <button className="mo-chip__clear" type="button" onClick={onClear} aria-label="Remove creator filter">×</button>
            </div>
        );
    }

    const settled = debounced === typed && !searching;

    return (
        <div className="mo-picker" onBlur={(event) => { if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false); }}>
            <input
                className="field"
                type="search"
                placeholder="Creator: username or email"
                aria-label="Filter by creator"
                autoComplete="off"
                value={text}
                onChange={(event) => { setText(event.target.value); setOpen(true); }}
                onFocus={() => setOpen(true)}
                onKeyDown={(event) => event.key === 'Escape' && setOpen(false)}
            />
            {open && typed && (
                <ul className="mo-suggestions">
                    {!settled && <li className="mo-suggestions__empty">Searching...</li>}
                    {settled && results.length === 0 && <li className="mo-suggestions__empty">No users found.</li>}
                    {settled && results.map((user) => (
                        <li key={user.id}>
                            <button className="mo-suggestion" type="button" onClick={() => { onSelect(user); setText(''); setOpen(false); }}>
                                <UserAvatar username={user.username} url={user.avatar_url} size={30} />
                                <span className="mo-suggestion__text"><strong>@{user.username}</strong><span>{user.email}</span></span>
                            </button>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}

function ModerationPanel({ onPhotoSelect }) {
    const [initial] = useState(() => savedFilters ?? DEFAULT_FILTERS);
    const [creator, setCreator] = useState(initial.creator);
    const [keywordInput, setKeywordInput] = useState(initial.keyword);
    const [sort, setSort] = useState(initial.sort);
    const [page, setPage] = useState(initial.page);
    const [photos, setPhotos] = useState([]);
    const [hasNextPage, setHasNextPage] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    // Review dialog.
    const [selectedPhoto, setSelectedPhoto] = useState(null);
    const [ratings, setRatings] = useState(null); // null = still loading
    const [dialogError, setDialogError] = useState('');
    const [dialogMessage, setDialogMessage] = useState('');
    const [deletingId, setDeletingId] = useState(null);

    const debouncedKeyword = useDebouncedValue(keywordInput.trim());
    const selectedId = selectedPhoto?.id;

    // Back to page 1 when the (debounced) search text changes.
    const [syncedKeyword, setSyncedKeyword] = useState(debouncedKeyword);
    if (syncedKeyword !== debouncedKeyword) {
        setSyncedKeyword(debouncedKeyword);
        setPage(1);
    }

    useEffect(() => {
        savedFilters = { creator, keyword: keywordInput, sort, page };
    }, [creator, keywordInput, sort, page]);

    // Load the photo list.
    useEffect(() => {
        let ignore = false;
        const sortOption = SORTS.find((option) => option.value === sort);
        const request = window.setTimeout(async () => {
            setLoading(true);
            setError('');
            try {
                const response = await api.get('/search/photos', {
                    params: {
                        user_id: creator?.id,
                        keyword: debouncedKeyword || undefined,
                        sort_by: sortOption.sortBy,
                        order: sortOption.order,
                        page,
                        page_size: PAGE_SIZE,
                    },
                });
                if (ignore) return;
                setPhotos(response.data);
                setHasNextPage(response.data.length === PAGE_SIZE);
            } catch (err) {
                if (!ignore) setError(getError(err, 'Could not load photos.'));
            } finally {
                if (!ignore) setLoading(false);
            }
        }, 0);
        return () => {
            ignore = true;
            window.clearTimeout(request);
        };
    }, [creator, debouncedKeyword, sort, page]);

    // Load the ratings of the photo being reviewed.
    useEffect(() => {
        if (!selectedId) return undefined;
        let ignore = false;
        api.get(`/photos/${selectedId}/ratings`)
            .then((response) => { if (!ignore) setRatings(response.data); })
            .catch((err) => {
                if (ignore) return;
                setDialogError(getError(err, 'Could not load ratings.'));
                setRatings([]);
            });
        return () => { ignore = true; };
    }, [selectedId]);

    // Escape closes the dialog.
    useEffect(() => {
        if (!selectedId) return undefined;
        const handleEscape = (event) => event.key === 'Escape' && setSelectedPhoto(null);
        window.addEventListener('keydown', handleEscape);
        return () => window.removeEventListener('keydown', handleEscape);
    }, [selectedId]);

    const hasActiveFilters = Boolean(creator || keywordInput || sort !== DEFAULT_FILTERS.sort);

    const selectCreator = (user) => { setCreator(user); setPage(1); };
    const clearCreator = () => { setCreator(null); setPage(1); };
    const handleReset = () => {
        setCreator(null);
        setKeywordInput('');
        setSort(DEFAULT_FILTERS.sort);
        setPage(1);
    };

    const openReview = (photo) => {
        setSelectedPhoto(photo);
        setRatings(null);
        setDialogError('');
        setDialogMessage('');
    };

    const handleDeleteRating = async (ratingId) => {
        if (!window.confirm('Delete this rating?')) return;
        try {
            setDeletingId(ratingId);
            setDialogError('');
            setDialogMessage('');
            await api.delete(`/photos/rate/${ratingId}`);
            const remaining = ratings.filter((rating) => rating.id !== ratingId);
            const average = remaining.length ? Math.round((remaining.reduce((sum, rating) => sum + rating.rate, 0) / remaining.length) * 100) / 100 : 0;
            setRatings(remaining);
            setPhotos((items) => items.map((photo) => photo.id === selectedId ? { ...photo, average_rating: average } : photo));
            setSelectedPhoto((photo) => ({ ...photo, average_rating: average }));
            setDialogMessage('Rating deleted.');
        } catch (err) {
            setDialogError(getError(err));
        } finally {
            setDeletingId(null);
        }
    };

    return (
        <main className="moderation-page">
            <header className="mo-header">
                <h2>Image moderation</h2>
                <p>Find a photo, review its ratings and remove abusive ones. Comments and photo deletion are on the photo page.</p>
            </header>

            <div className="mo-toolbar" role="search">
                <CreatorPicker creator={creator} onSelect={selectCreator} onClear={clearCreator} />
                <input className="field" type="search" placeholder="Search descriptions..." aria-label="Search descriptions" value={keywordInput} onChange={(event) => setKeywordInput(event.target.value)} />
                <select className="field" aria-label="Sort photos" value={sort} onChange={(event) => { setSort(event.target.value); setPage(1); }}>
                    {SORTS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                </select>
                <button className="btn btn-secondary" type="button" onClick={handleReset} disabled={!hasActiveFilters}>Reset</button>
            </div>

            {error && <p className="error-message" role="alert">{error}</p>}

            <section>
                <div className="mo-section-header">
                    <h3>{creator ? `Photos by @${creator.username}` : 'All photos'}</h3>
                    <span>{photos.length} on this page</span>
                </div>

                {!loading && photos.length === 0 && !error ? (
                    <div className="feed-status">
                        <p>No photos match these filters.</p>
                    </div>
                ) : (
                    <div className="mo-table-wrap" aria-busy={loading}>
                        <table className="mo-table">
                            <thead>
                                <tr>
                                    <th scope="col">Photo</th>
                                    <th scope="col">Creator</th>
                                    <th scope="col">Rating</th>
                                    <th scope="col">Uploaded</th>
                                    <th scope="col">Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                {photos.map((photo) => {
                                    const rating = Number(photo.average_rating || 0);
                                    return (
                                        <tr key={photo.id}>
                                            <td>
                                                <div className="mo-photo">
                                                    <img className="mo-thumb" src={photo.url} alt="" loading="lazy" />
                                                    <span className={photo.description ? 'mo-desc' : 'mo-desc is-empty'}>{photo.description || 'No description'}</span>
                                                </div>
                                            </td>
                                            <td>
                                                <span className="mo-creator">
                                                    <UserAvatar username={photo.username} url={photo.avatar_url} size={28} />
                                                    @{photo.username}
                                                </span>
                                            </td>
                                            <td>{rating ? <span className="mo-stars">★ {rating.toFixed(1)}</span> : <span className="mo-muted">Not rated</span>}</td>
                                            <td>{formatDate(photo.created_at)}</td>
                                            <td><button className="btn btn-secondary" type="button" onClick={() => openReview(photo)}>Moderate</button></td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                )}

                <nav className="mo-pagination" aria-label="Pagination">
                    <button className="btn btn-secondary" type="button" onClick={() => setPage((current) => current - 1)} disabled={loading || page === 1}>‹ Previous</button>
                    <span>Page {page}</span>
                    <button className="btn btn-secondary" type="button" onClick={() => setPage((current) => current + 1)} disabled={loading || !hasNextPage}>Next ›</button>
                </nav>
            </section>

            {selectedPhoto && (
                <div className="modal-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && setSelectedPhoto(null)}>
                    <section className="mo-dialog" role="dialog" aria-modal="true" aria-labelledby="mo-dialog-title">
                        <div className="modal-heading">
                            <h3 id="mo-dialog-title">Moderate photo</h3>
                            <button className="icon-button" type="button" onClick={() => setSelectedPhoto(null)} aria-label="Close dialog">×</button>
                        </div>

                        {dialogError && <p className="error-message" role="alert">{dialogError}</p>}
                        {dialogMessage && <p className="success-message" role="status">{dialogMessage}</p>}

                        <div className="mo-dialog__body">
                            <div>
                                <img className="mo-preview" src={selectedPhoto.url} alt={selectedPhoto.description || 'Photo under moderation'} />
                                <div className="mo-meta">
                                    <p>{selectedPhoto.description || <i className="mo-muted">No description</i>}</p>
                                    <p className="mo-creator"><UserAvatar username={selectedPhoto.username} url={selectedPhoto.avatar_url} size={24} />@{selectedPhoto.username}</p>
                                    <p className="mo-muted">Uploaded {formatDate(selectedPhoto.created_at)}</p>
                                </div>
                            </div>

                            <div>
                                <div className="mo-ratings-header">
                                    <h4>Ratings</h4>
                                    <span>{ratings ? `${ratings.length} total · average ${Number(selectedPhoto.average_rating || 0).toFixed(1)}` : ''}</span>
                                </div>
                                {ratings === null ? (
                                    <div className="mo-empty" role="status">Loading ratings...</div>
                                ) : ratings.length === 0 ? (
                                    <div className="mo-empty">This photo has no ratings.</div>
                                ) : (
                                    <ul className="mo-rating-list">
                                        {ratings.map((rating) => (
                                            <li className="mo-rating-row" key={rating.id}>
                                                <div>
                                                    <strong className="mo-stars">★ {rating.rate} / 5</strong>
                                                    <small>{rating.username ? `@${rating.username}` : `User #${rating.user_id}`}</small>
                                                </div>
                                                <button className="btn btn-secondary mo-btn-danger" type="button" onClick={() => handleDeleteRating(rating.id)} disabled={deletingId === rating.id}>
                                                    {deletingId === rating.id ? 'Deleting...' : 'Delete'}
                                                </button>
                                            </li>
                                        ))}
                                    </ul>
                                )}
                            </div>
                        </div>

                        <div className="modal-actions">
                            <button className="btn btn-secondary" type="button" onClick={() => setSelectedPhoto(null)}>Close</button>
                            {onPhotoSelect && <button className="btn btn-primary" type="button" onClick={() => onPhotoSelect(selectedPhoto.id)}>Open photo page</button>}
                        </div>
                    </section>
                </div>
            )}
        </main>
    );
}

export default ModerationPanel;
