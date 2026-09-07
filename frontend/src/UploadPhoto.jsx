import React, { useState } from 'react';
import api from './api';

function UploadPhoto({ onUploadSuccess }) {
    const [file, setFile] = useState(null);
    const [preview, setPreview] = useState(''); // Стан для тимчасового лінку передперегляду
    const [description, setDescription] = useState('');
    const [tags, setTags] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    // Новий стан: тепер форма за замовчуванням схована (false)
    const [isOpen, setIsOpen] = useState(false);

    const handleFileChange = (e) => {
        const selectedFile = e.target.files[0];
        if (selectedFile) {
            setFile(selectedFile);
            // Створюємо локальне посилання для миттєвого відображення картинки на екрані
            setPreview(URL.createObjectURL(selectedFile));
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!file) {
            setError('Будь ласка, виберіть файл зображення.');
            return;
        }

        setLoading(true);
        setError('');
        setSuccess('');

        const formData = new FormData();
        formData.append('file', file);
        if (description) formData.append('description', description);
        if (tags) formData.append('tags', tags);

        try {
            await api.post('/photos/', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });

            setSuccess('Світлину успішно завантажено в Cloudinary!');
            setFile(null);
            setPreview(''); // Очищуємо передперегляд
            setDescription('');
            setTags('');

            if (onUploadSuccess) onUploadSuccess();

            // Автоматично закриваємо форму через 2 секунди після успіху
            setTimeout(() => {
                setIsOpen(false);
                setSuccess('');
            }, 2000);

        } catch (err) {
            setError(err.response?.data?.detail || 'Помилка під час завантаження фото.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ marginBottom: '30px' }}>

            {/* КНОПКА-ПЕРЕМИКАЧ (Відкрити / Сховати форму) */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                style={{
                    padding: '10px 20px',
                    backgroundColor: isOpen ? '#6c757d' : '#007bff',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontWeight: 'bold',
                    marginBottom: '15px'
                }}
            >
                {isOpen ? 'Скасувати завантаження' : 'Upload New Photo'}
            </button>

            {/* ЯКЩО isOpen === true — ПОКАЗУЄМО ФОРМУ, ЯКЩО false — ВОНА СХОВАНА */}
            {isOpen && (
                <div style={{ backgroundColor: '#f8f9fa', padding: '20px', borderRadius: '8px', border: '1px solid #ddd' }}>
                    <h3>Завантажити нову світлину</h3>

                    {error && <p style={{ color: 'red' }}>{error}</p>}
                    {success && <p style={{ color: 'green' }}>{success}</p>}

                    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                        <div>
                            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Оберіть файл:</label>
                            <input
                                type="file"
                                accept="image/*"
                                onChange={handleFileChange}
                                required
                            />
                        </div>

                        {/* БЛОК ПЕРЕДПЕРЕГЛЯДУ: Показуємо картинку, тільки якщо файл обрано */}
                        {preview && (
                            <div style={{ marginTop: '10px', textAlign: 'center' }}>
                                <p style={{ margin: '0 0 5px 0', fontSize: '14px', color: '#666' }}>Попередній перегляд:</p>
                                <img
                                    src={preview}
                                    alt="Preview"
                                    style={{ maxWidth: '100%', maxHeight: '200px', borderRadius: '6px', objectFit: 'contain', border: '1px solid #ccc' }}
                                />
                            </div>
                        )}

                        <div>
                            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Опис світлини:</label>
                            <textarea
                                placeholder="Напишіть щось про це фото..."
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                style={{ width: '100%', padding: '8px', minHeight: '60px', boxSizing: 'border-box' }}
                            />
                        </div>

                        <div>
                            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Теги (через кому, макс. 5):</label>
                            <input
                                type="text"
                                placeholder="summer, sunset, vacation"
                                value={tags}
                                onChange={(e) => setTags(e.target.value)}
                                style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            style={{
                                padding: '10px',
                                backgroundColor: loading ? '#6c757d' : '#28a745',
                                color: 'white',
                                border: 'none',
                                borderRadius: '4px',
                                cursor: loading ? 'not-allowed' : 'pointer',
                                fontWeight: 'bold'
                            }}
                        >
                            {loading ? 'Завантаження на Cloudinary...' : 'Опублікувати світлину'}
                        </button>
                    </form>
                </div>
            )}
        </div>
    );
}

export default UploadPhoto;
