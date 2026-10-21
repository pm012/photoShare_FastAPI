import { useEffect, useState } from 'react';
import UploadPhoto from './UploadPhoto';
import api from './api';
import './PhotoFeed.css';

const PAGE_SIZE = 20;
const MAX_VISIBLE_TAGS = 3;

// "param" is the query parameter the backend expects for each search mode.
const SEARCH_FIELDS = [
    { value: 'description', label: 'Description', param: 'keyword' },
    { value: 'tag', label: 'Tag', param: 'tag' },
];
const SORT_OPTIONS = [
    { value: 'date', label: 'Date' },
    { value: 'rating', label: 'Rating' },
];
const RATING_OPTIONS = [
    { value: '', label: 'Any rating' },
    { value: '4', label: '4★ and up' },
    { value: '3', label: '3★ and up' },
    { value: '2', label: '2★ and up' },
];
const DEFAULT_FILTERS = { searchField: 'description', query: '', sortBy: 'date', order: 'desc', minRating: '' };

// Returns `value` only after it has stopped changing for `delay` ms.
function useDebouncedValue(value, delay = 350) {
    const [debounced, setDebounced] = useState(value);
    useEffect(() => {
        const timer = window.setTimeout(() => setDebounced(value), delay);
        return () => window.clearTimeout(timer);
    }, [value, delay]);
    return debounced;
}

function StarRating({ value }) {
    if (!value) return <p className="photo-rating photo-rating--empty">Not rated yet</p>;
    return (
        <p className="photo-rating">
            <span className="rating-stars" role="img" aria-label={`Rating ${value.toFixed(1)} out of 5`}>
                {[1, 2, 3, 4, 5].map((star) => (
                    <span className={star <= Math.round(value) ? 'rating-star is-filled' : 'rating-star'} key={star}>★</span>
                ))}
            </span>
            <span aria-hidden="true">{value.toFixed(1)}</span>
        </p>
    );
}

function PhotoCard({ photo, onOpen, onOpenProfile, onZoom, onTagClick }) {
    const tags = photo.tags || [];
    const hiddenTags = tags.length - MAX_VISIBLE_TAGS;

    return (
        <article className="photo-card">
            <div className="photo-media">
                <img src={photo.url} alt={photo.description || `Photo by @${photo.username}`} loading="lazy" />
                <button className="photo-zoom" type="button" onClick={() => onZoom(photo)} aria-label="View full-size image">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                        <path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7" />
                    </svg>
                </button>
            </div>

            <div className="photo-body">
                <button className="photo-author" type="button" onClick={() => onOpenProfile(photo.username)} aria-label={`Open profile of ${photo.username}`}>
                    <span className="photo-author__avatar" aria-hidden="true">{photo.username?.[0]?.toUpperCase()}</span>
                    <span className="photo-author__name">@{photo.username}</span>
                </button>

                <button className="photo-open" type="button" onClick={() => onOpen(photo.id)}>
                    <span className="photo-description">{photo.description || <i>No description</i>}</span>
                </button>

                <StarRating value={Number(photo.average_rating || 0)} />

                {tags.length > 0 && (
                    <ul className="tag-list" aria-label="Tags">
                        {tags.slice(0, MAX_VISIBLE_TAGS).map((tag) => (
                            <li key={tag.id}>
                                <button className="tag" type="button" onClick={() => onTagClick(tag.name)} title={`Show photos tagged #${tag.name}`}>#{tag.name}</button>
                            </li>
                        ))}
                        {hiddenTags > 0 && <li className="tag">+{hiddenTags}</li>}
                    </ul>
                )}
            </div>
        </article>
    );
}

function SkeletonGrid() {
    return (
        <div className="photo-grid" aria-hidden="true">
            {Array.from({ length: 6 }, (_, index) => (
                <div className="photo-card photo-card--skeleton" key={index}>
                    <div className="photo-media" />
                    <div className="photo-body">
                        <div className="skeleton-line short" />
                        <div className="skeleton-line" />
                        <div className="skeleton-line short" />
                    </div>
                </div>
            ))}
        </div>
    );
}

function PhotoFeed({ onPhotoSelect, onProfileSelect }) {
    const [photos, setPhotos] = useState([]);
    const [filters, setFilters] = useState(DEFAULT_FILTERS);
    const [page, setPage] = useState(1);
    const [hasNextPage, setHasNextPage] = useState(false);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(true);
    const [reloadKey, setReloadKey] = useState(0);
    const [isUploadOpen, setIsUploadOpen] = useState(false);
    const [lightboxPhoto, setLightboxPhoto] = useState(null);

    const { searchField, query, sortBy, order, minRating } = filters;
    const debouncedQuery = useDebouncedValue(query);

    // Go back to page 1 when the (debounced) search text changes.
    const [syncedQuery, setSyncedQuery] = useState(debouncedQuery);
    if (syncedQuery !== debouncedQuery) {
        setSyncedQuery(debouncedQuery);
        setPage(1);
    }

    // Load photos whenever a filter, the sort, or the page changes.
    useEffect(() => {
        let ignore = false;
        const request = window.setTimeout(async () => {
            setLoading(true);
            setError('');
            try {
                const params = { sort_by: sortBy, order, page, page_size: PAGE_SIZE, min_rating: minRating || undefined };
                const text = debouncedQuery.trim();
                if (text) params[SEARCH_FIELDS.find((field) => field.value === searchField).param] = text;

                const response = await api.get('/search/photos', { params });
                if (ignore) return;
                setPhotos(response.data);
                setHasNextPage(response.data.length === PAGE_SIZE);
            } catch (err) {
                if (!ignore) setError(err.response?.data?.detail || 'Could not load photos.');
            } finally {
                if (!ignore) setLoading(false);
            }
        }, 0);
        return () => {
            ignore = true;
            window.clearTimeout(request);
        };
    }, [debouncedQuery, searchField, sortBy, order, minRating, page, reloadKey]);

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

    // Change a filter and return to page 1.
    const updateFilters = (patch) => {
        setFilters((previous) => ({ ...previous, ...patch }));
        setPage(1);
    };

    // Clicking the active column flips the direction; clicking another column sorts by it (newest/highest first).
    const handleSort = (value) => {
        if (sortBy === value) updateFilters({ order: order === 'desc' ? 'asc' : 'desc' });
        else updateFilters({ sortBy: value, order: 'desc' });
    };

    const handleTagClick = (name) => setFilters((previous) => ({ ...previous, searchField: 'tag', query: name }));
    const handleReset = () => updateFilters(DEFAULT_FILTERS);

    const goToPage = (nextPage) => {
        setPage(nextPage);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    const hasActiveFilters = Boolean(query || minRating || sortBy !== DEFAULT_FILTERS.sortBy || order !== DEFAULT_FILTERS.order);
    const currentField = SEARCH_FIELDS.find((field) => field.value === searchField);
    const isInitialLoad = loading && photos.length === 0;

    return (
        <main className="feed-page">
            <header className="feed-header">
                <div>
                    <h2>Photo feed</h2>
                    <p className="feed-subtitle">Ideas, moments, and stories from the community.</p>
                </div>
                <button className="btn btn-primary" type="button" onClick={() => setIsUploadOpen(true)}>
                    <span aria-hidden="true">+</span> Upload photo
                </button>
            </header>

            <div className="feed-toolbar" role="search">
                <div className="feed-filters">
                    <div className="search-group">
                        <select className="field" aria-label="Search by" value={searchField} onChange={(e) => updateFilters({ searchField: e.target.value })}>
                            {SEARCH_FIELDS.map((field) => <option key={field.value} value={field.value}>{field.label}</option>)}
                        </select>
                        <input
                            className="field"
                            type="search"
                            placeholder={`Search by ${currentField.label.toLowerCase()}...`}
                            aria-label="Search query"
                            value={query}
                            onChange={(e) => setFilters((previous) => ({ ...previous, query: e.target.value }))}
                        />
                    </div>
                    <select className="field" aria-label="Minimum rating" value={minRating} onChange={(e) => updateFilters({ minRating: e.target.value })}>
                        {RATING_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                    </select>
                    <button className="btn btn-secondary" type="button" onClick={handleReset} disabled={!hasActiveFilters}>Reset</button>
                </div>

                <div className="sort-bar" role="group" aria-label="Sort photos">
                    <span className="sort-bar__label">Sort by</span>
                    {SORT_OPTIONS.map((option) => {
                        const isActive = sortBy === option.value;
                        const direction = order === 'asc' ? 'ascending' : 'descending';
                        return (
                            <button
                                key={option.value}
                                className={isActive ? 'btn btn-secondary sort-chip is-active' : 'btn btn-secondary sort-chip'}
                                type="button"
                                onClick={() => handleSort(option.value)}
                                aria-pressed={isActive}
                                aria-label={isActive ? `Sorted by ${option.label}, ${direction}. Click to reverse.` : `Sort by ${option.label}`}
                            >
                                {option.label}
                                <span className="sort-chip__arrow" aria-hidden="true">{isActive ? (order === 'asc' ? '↑' : '↓') : '↕'}</span>
                            </button>
                        );
                    })}
                </div>
            </div>

            {error && (
                <div className="error-message feed-error" role="alert">
                    <span>{error}</span>
                    <button className="btn btn-secondary" type="button" onClick={() => setReloadKey((key) => key + 1)}>Try again</button>
                </div>
            )}

            {isInitialLoad ? (
                <SkeletonGrid />
            ) : photos.length === 0 ? (
                !error && (
                    <div className="feed-status">
                        {page > 1 ? (
                            <>
                                <p>There are no more photos.</p>
                                <button className="btn btn-secondary" type="button" onClick={() => goToPage(page - 1)}>‹ Previous</button>
                            </>
                        ) : hasActiveFilters ? (
                            <>
                                <p>No photos match your search.</p>
                                <button className="btn btn-secondary" type="button" onClick={handleReset}>Reset filters</button>
                            </>
                        ) : (
                            <>
                                <p>No photos yet. Be the first to upload one.</p>
                                <button className="btn btn-primary" type="button" onClick={() => setIsUploadOpen(true)}>Upload photo</button>
                            </>
                        )}
                    </div>
                )
            ) : (
                <>
                    <div className="photo-grid" aria-busy={loading}>
                        {photos.map((photo) => (
                            <PhotoCard
                                key={photo.id}
                                photo={photo}
                                onOpen={onPhotoSelect}
                                onOpenProfile={onProfileSelect}
                                onZoom={setLightboxPhoto}
                                onTagClick={handleTagClick}
                            />
                        ))}
                    </div>
                    <nav className="pagination" aria-label="Pagination">
                        <button className="btn btn-secondary" type="button" onClick={() => goToPage(page - 1)} disabled={page === 1 || loading}>‹ Previous</button>
                        <span>Page {page}</span>
                        <button className="btn btn-secondary" type="button" onClick={() => goToPage(page + 1)} disabled={!hasNextPage || loading}>Next ›</button>
                    </nav>
                </>
            )}

            {isUploadOpen && (
                <UploadPhoto
                    onClose={() => setIsUploadOpen(false)}
                    onUploadSuccess={() => { setPage(1); setReloadKey((key) => key + 1); }}
                />
            )}

            {lightboxPhoto && (
                <div className="lightbox-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && setLightboxPhoto(null)}>
                    <section className="lightbox" role="dialog" aria-modal="true" aria-label="Full-size photo viewer">
                        <button className="icon-button lightbox-close" type="button" onClick={() => setLightboxPhoto(null)} aria-label="Close viewer">×</button>
                        <img src={lightboxPhoto.url} alt={lightboxPhoto.description || 'Full-size photo'} />
                    </section>
                </div>
            )}
        </main>
    );
}

export default PhotoFeed;