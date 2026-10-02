import { useCallback, useEffect, useState } from 'react';
import UploadPhoto from './UploadPhoto';
import api from './api';

function PhotoFeed({ onPhotoSelect, onProfileSelect }) {
    const [photos, setPhotos] = useState([]);
    const [keyword, setKeyword] = useState('');
    const [tag, setTag] = useState('');
    const [sortBy, setSortBy] = useState('date');
    const [order, setOrder] = useState('desc');
    const [minRating, setMinRating] = useState('');
    const [page, setPage] = useState(1);
    const [hasNextPage, setHasNextPage] = useState(false);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(true);
    const [isUploadOpen, setIsUploadOpen] = useState(false);
    const [lightboxPhoto, setLightboxPhoto] = useState(null);

    // Load photos from the backend.
    const fetchPhotos = useCallback(async (requestedPage = page) => {
        try {
            setError('');
            setLoading(true);
            // Build the advanced search query parameters.
            const response = await api.get('/search/photos', {
                params: {
                    keyword: keyword || undefined, // Omit empty values.
                    tag: tag || undefined,
                    sort_by: sortBy,
                    order: order,
                    page: requestedPage,
                    page_size: 20,
                    min_rating: minRating || undefined,
                }
            });
            setPhotos(response.data);
            setPage(requestedPage);
            setHasNextPage(response.data.length === 20);
        } catch (err) {
            setError(err.response?.data?.detail || 'Could not load photos.');
        } finally {
            setLoading(false);
        }
    }, [keyword, minRating, order, page, sortBy, tag]);

    // Fetch photos on initial load and whenever the sort options change.
    useEffect(() => {
        const request = window.setTimeout(fetchPhotos, 350);
        return () => window.clearTimeout(request);
    }, [fetchPhotos]);

    useEffect(() => {
        const handleEscape = (event) => {
            if (event.key === 'Escape') {
                setIsUploadOpen(false);
                setLightboxPhoto(null);
            }
        };
        window.addEventListener('keydown', handleEscape);
        return () => window.removeEventListener('keydown', handleEscape);
    }, []);

    const handleSearchSubmit = (e) => {
        e.preventDefault();
        fetchPhotos(1);
    };

    const handleResetFilters = () => {
        setKeyword('');
        setTag('');
        setSortBy('date');
        setOrder('desc');
        setMinRating('');
        setPage(1);
    };

    return (
        <main className="feed-page">
            <header className="feed-header">
                <div>
                    <p className="eyebrow">PhotoShare / explore</p>
                    <h2>Photo feed</h2>
                    <p className="feed-subtitle">Ideas, moments, and stories from the community.</p>
                </div>
                <button className="primary-button upload-trigger" onClick={() => setIsUploadOpen(true)}>
                    <span aria-hidden="true">+</span> Upload photo
                </button>
            </header>

            {/* Search and filtering controls. */}
            <form className="feed-controls" onSubmit={handleSearchSubmit}>
                <div className="feed-control-row feed-search-row">
                    <input className="search-input" type="text" placeholder="Search descriptions..." value={keyword} onChange={(e) => { setKeyword(e.target.value); setPage(1); }} aria-label="Search descriptions" />
                    <input type="text" placeholder="Tag..." value={tag} onChange={(e) => { setTag(e.target.value); setPage(1); }} aria-label="Search by tag" />
                    <button className="primary-button search-button" type="submit">Search</button>
                </div>
                <div className="feed-control-row feed-sort-row">
                    <label className="select-field"><span>Sort by</span><select value={sortBy} onChange={(e) => { setSortBy(e.target.value); setPage(1); }}>
                        <option value="date">Date</option>
                        <option value="rating">Rating</option>
                    </select></label>
                    <label className="select-field"><span>Order</span><select aria-label="Sort order" value={order} onChange={(e) => { setOrder(e.target.value); setPage(1); }}>
                        <option value="desc">Descending</option>
                        <option value="asc">Ascending</option>
                    </select></label>
                    <label className="select-field"><span>Rating</span><select aria-label="Minimum rating" value={minRating} onChange={(e) => { setMinRating(e.target.value); setPage(1); }}>
                        <option value="">Any</option>
                        <option value="4">4 stars and up</option>
                        <option value="3">3 stars and up</option>
                        <option value="2">2 stars and up</option>
                    </select></label>
                    <button className="secondary-button reset-button" type="button" onClick={handleResetFilters}>Clear</button>
                </div>
            </form>

            {error && <p className="error-message" role="alert">{error}</p>}

            {/* Photo grid. */}
            {loading ? (
                <div className="feed-status" role="status">Loading photos...</div>
            ) : photos.length === 0 ? (
                <div className="feed-status">No photos found. Be the first to upload one.</div>
            ) : (
                <div className="photo-grid">
                    {photos.map((photo) => (
                        <article className="photo-card" key={photo.id} onClick={() => onPhotoSelect(photo.id)} onKeyDown={(event) => event.key === 'Enter' && onPhotoSelect(photo.id)} tabIndex="0" role="button">
                            <button className="photo-image-button" type="button" onClick={(event) => { event.stopPropagation(); setLightboxPhoto(photo); }} aria-label="View full-size image">
                                <img src={photo.url} alt={photo.description || 'PhotoShare photo'} />
                            </button>
                            <div className="photo-card-body">
                                <button className="photo-author" onClick={(event) => { event.stopPropagation(); onProfileSelect(photo.username); }}>@{photo.username}</button>
                                <p className="photo-rating" aria-label={`Rating ${photo.average_rating || '0.0'} out of 5`}><span className="stars" aria-hidden="true">{[1, 2, 3, 4, 5].map((star) => <span className={star <= Math.round(photo.average_rating || 0) ? 'star filled' : 'star'} key={star}>★</span>)}</span><span>{Number(photo.average_rating || 0).toFixed(1)}</span></p>
                                <p className="photo-description">
                                    {photo.description || <i>No description</i>}
                                </p>
                                <div className="tag-list">
                                    {photo.tags?.map((tag) => (
                                        <span className="tag" key={tag.id}>
                                            #{tag.name}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        </article>
                    ))}
                </div>
            )}
            {!loading && photos.length > 0 && <div className="pagination-controls"><button className="secondary-button" onClick={() => fetchPhotos(page - 1)} disabled={page === 1 || loading}>← Previous</button><span>Page {page}</span><button className="secondary-button" onClick={() => fetchPhotos(page + 1)} disabled={!hasNextPage || loading}>Next →</button></div>}
            {isUploadOpen && <UploadPhoto onClose={() => setIsUploadOpen(false)} onUploadSuccess={fetchPhotos} />}
            {lightboxPhoto && <div className="lightbox-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && setLightboxPhoto(null)}><section className="lightbox" role="dialog" aria-modal="true" aria-label="Full-size photo viewer"><button className="icon-button lightbox-close" type="button" onClick={() => setLightboxPhoto(null)} aria-label="Close viewer">×</button><img src={lightboxPhoto.url} alt={lightboxPhoto.description || 'Full-size photo'} /></section></div>}
        </main>
    );
}

export default PhotoFeed;
