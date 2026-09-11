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

    // Функція для завантаження фотографій з нашого бекенду
    const fetchPhotos = useCallback(async (requestedPage = page) => {
        try {
            setError('');
            setLoading(true);
            // Формуємо query-параметри для нашого розширеного пошуку
            const response = await api.get('/search/photos', {
                params: {
                    keyword: keyword || undefined, // Якщо порожньо — не передаємо
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
            setError(err.response?.data?.detail || 'Не вдалося завантажити світлини.');
        } finally {
            setLoading(false);
        }
    }, [keyword, minRating, order, page, sortBy, tag]);

    // Автоматично викликаємо fetchPhotos при першому завантаженні сторінки,
    // а також кожен раз, коли користувач змінює сортування (sortBy чи order)
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
                    <h2>Стрічка світлин</h2>
                    <p className="feed-subtitle">Ідеї, моменти та історії спільноти в одному місці.</p>
                </div>
                <button className="primary-button upload-trigger" onClick={() => setIsUploadOpen(true)}>
                    <span aria-hidden="true">+</span> Завантажити фото
                </button>
            </header>

            {/* БЛОК ПОШУКУ ТА ФІЛЬТРАЦІЇ (Панель керування для UI) */}
            <form className="feed-controls" onSubmit={handleSearchSubmit}>
                <div className="feed-control-row feed-search-row">
                    <input className="search-input" type="text" placeholder="Пошук за описом..." value={keyword} onChange={(e) => { setKeyword(e.target.value); setPage(1); }} aria-label="Пошук за описом" />
                    <input type="text" placeholder="Тег..." value={tag} onChange={(e) => { setTag(e.target.value); setPage(1); }} aria-label="Пошук за тегом" />
                    <button className="primary-button search-button" type="submit">Шукати</button>
                </div>
                <div className="feed-control-row feed-sort-row">
                    <label className="select-field"><span>Сортувати за</span><select value={sortBy} onChange={(e) => { setSortBy(e.target.value); setPage(1); }}>
                        <option value="date">Датою</option>
                        <option value="rating">Рейтингом</option>
                    </select></label>
                    <label className="select-field"><span>Порядок</span><select aria-label="Порядок сортування" value={order} onChange={(e) => { setOrder(e.target.value); setPage(1); }}>
                        <option value="desc">Спаданням</option>
                        <option value="asc">Зростанням</option>
                    </select></label>
                    <label className="select-field"><span>Рейтинг</span><select aria-label="Мінімальний рейтинг" value={minRating} onChange={(e) => { setMinRating(e.target.value); setPage(1); }}>
                        <option value="">Будь-який</option>
                        <option value="4">Від 4 зірок</option>
                        <option value="3">Від 3 зірок</option>
                        <option value="2">Від 2 зірок</option>
                    </select></label>
                    <button className="secondary-button reset-button" type="button" onClick={handleResetFilters}>Очистити</button>
                </div>
            </form>

            {error && <p className="error-message" role="alert">{error}</p>}

            {/* СТРІЧКА СВІТЛИН (Мережа карток у стилі Instagram) */}
            {loading ? (
                <div className="feed-status" role="status">Завантажуємо стрічку...</div>
            ) : photos.length === 0 ? (
                <div className="feed-status">Світлин не знайдено. Будьте першим, хто завантажить фото.</div>
            ) : (
                <div className="photo-grid">
                    {photos.map((photo) => (
                        <article className="photo-card" key={photo.id} onClick={() => onPhotoSelect(photo.id)} onKeyDown={(event) => event.key === 'Enter' && onPhotoSelect(photo.id)} tabIndex="0" role="button">
                            <button className="photo-image-button" type="button" onClick={(event) => { event.stopPropagation(); setLightboxPhoto(photo); }} aria-label="Відкрити повнорозмірне зображення">
                                <img src={photo.url} alt={photo.description || 'Світлина PhotoShare'} />
                            </button>
                            <div className="photo-card-body">
                                <button className="photo-author" onClick={(event) => { event.stopPropagation(); onProfileSelect(photo.username); }}>@{photo.username}</button>
                                <p className="photo-rating" aria-label={`Рейтинг ${photo.average_rating || '0.0'} з 5`}><span className="stars" aria-hidden="true">{[1, 2, 3, 4, 5].map((star) => <span className={star <= Math.round(photo.average_rating || 0) ? 'star filled' : 'star'} key={star}>★</span>)}</span><span>{Number(photo.average_rating || 0).toFixed(1)}</span></p>
                                <p className="photo-description">
                                    {photo.description || <i>Без опису</i>}
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
            {!loading && photos.length > 0 && <div className="pagination-controls"><button className="secondary-button" onClick={() => fetchPhotos(page - 1)} disabled={page === 1 || loading}>← Попередня</button><span>Сторінка {page}</span><button className="secondary-button" onClick={() => fetchPhotos(page + 1)} disabled={!hasNextPage || loading}>Наступна →</button></div>}
            {isUploadOpen && <UploadPhoto onClose={() => setIsUploadOpen(false)} onUploadSuccess={fetchPhotos} />}
            {lightboxPhoto && <div className="lightbox-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && setLightboxPhoto(null)}><section className="lightbox" role="dialog" aria-modal="true" aria-label="Повнорозмірний перегляд фото"><button className="icon-button lightbox-close" type="button" onClick={() => setLightboxPhoto(null)} aria-label="Закрити перегляд">×</button><img src={lightboxPhoto.url} alt={lightboxPhoto.description || 'Повнорозмірна світлина'} /></section></div>}
        </main>
    );
}

export default PhotoFeed;
