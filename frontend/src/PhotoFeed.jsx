import React, { useState, useEffect } from 'react';
import UploadPhoto from './UploadPhoto';
import api from './api';

function PhotoFeed() {
    const [photos, setPhotos] = useState([]);
    const [keyword, setKeyword] = useState('');
    const [sortBy, setSortBy] = useState('date');
    const [order, setOrder] = useState('desc');
    const [error, setError] = useState('');

    // Функція для завантаження фотографій з нашого бекенду
    const fetchPhotos = async () => {
        try {
            setError('');
            // Формуємо query-параметри для нашого розширеного пошуку
            const response = await api.get('/search/photos', {
                params: {
                    keyword: keyword || undefined, // Якщо порожньо — не передаємо
                    sort_by: sortBy,
                    order: order
                }
            });
            setPhotos(response.data);
        } catch (err) {
            setError(err.response?.data?.detail || 'Не вдалося завантажити світлини.');
        }
    };

    // Автоматично викликаємо fetchPhotos при першому завантаженні сторінки,
    // а також кожен раз, коли користувач змінює сортування (sortBy чи order)
    useEffect(() => {
        fetchPhotos();
    }, [sortBy, order]);

    const handleSearchSubmit = (e) => {
        e.preventDefault();
        fetchPhotos(); // Шукаємо при натисканні на кнопку
    };

    return (
        <div style={{ maxWidth: '900px', margin: '30px auto', padding: '0 20px' }}>
            <h2>Стрічка світлин PhotoShare</h2>

            {/* 2. ВМОНТУВАЛИ ФОРМУ ЗАВАНТАЖЕННЯ НАД СТРІЧКОЮ */}
            {/* Передаємо функцію fetchPhotos, щоб стрічка сама оновилася після завантаження нового фото */}
            <UploadPhoto onUploadSuccess={fetchPhotos} />

            {/* БЛОК ПОШУКУ ТА ФІЛЬТРАЦІЇ (Панель керування для UI) */}
            <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: '10px', marginBottom: '20px', flexWrap: 'wrap', alignItems: 'center' }}>
                <input
                    type="text"
                    placeholder="Пошук за описом..."
                    value={keyword}
                    onChange={(e) => setKeyword(e.target.value)}
                    style={{ padding: '8px', flex: '1', minWidth: '200px' }}
                />
                <button type="submit" style={{ padding: '8px 15px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                    Шукати
                </button>

                <label>Сортувати за:</label>
                <select value={sortBy} onChange={(e) => setSortBy(e.target.value)} style={{ padding: '8px' }}>
                    <option value="date">Датою</option>
                    <option value="rating">Рейтингом</option>
                </select>

                <select value={order} onChange={(e) => setOrder(e.target.value)} style={{ padding: '8px' }}>
                    <option value="desc">Спаданням (New/High)</option>
                    <option value="asc">Зростанням (Old/Low)</option>
                </select>
            </form>

            {error && <p style={{ color: 'red' }}>{error}</p>}

            {/* СТРІЧКА СВІТЛИН (Мережа карток у стилі Instagram) */}
            {photos.length === 0 ? (
                <p style={{ textAlign: 'center', color: '#666' }}>Світлин не знайдено. Будьте першим, хто завантажить фото!</p>
            ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '20px' }}>
                    {photos.map((photo) => (
                        <div key={photo.id} style={{ border: '1px solid #ddd', borderRadius: '8px', overflow: 'hidden', backgroundColor: '#fff', boxShadow: '0 2px 5px rgba(0,0,0,0.1)' }}>

                            {/* Відображаємо реальне зображення з Cloudinary за лінком з бази */}
                            <img
                                src={photo.url}
                                alt={photo.description}
                                style={{ width: '100%', height: '200px', objectFit: 'cover' }}
                            />

                            <div style={{ padding: '15px' }}>
                                <p style={{ fontWeight: 'bold', margin: '0 0 10px 0' }}>
                                    ⭐ Рейтинг: {photo.average_rating || '0.0'}
                                </p>
                                <p style={{ margin: '0 0 10px 0', color: '#333' }}>
                                    {photo.description || <i>Без опису</i>}
                                </p>

                                {/* Виводимо список тегів */}
                                <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
                                    {photo.tags?.map((tag) => (
                                        <span key={tag.id} style={{ backgroundColor: '#e9ecef', padding: '3px 8px', borderRadius: '12px', fontSize: '12px', color: '#495057' }}>
                                            #{tag.name}
                                        </span>
                                    ))}
                                </div>
                            </div>

                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default PhotoFeed;
