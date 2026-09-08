import { useEffect, useRef, useState } from 'react';
import api from './api';

function UploadPhoto({ onUploadSuccess, onClose }) {
    const [file, setFile] = useState(null);
    const [preview, setPreview] = useState('');
    const [description, setDescription] = useState('');
    const [tags, setTags] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const fileInputRef = useRef(null);

    useEffect(() => () => preview && URL.revokeObjectURL(preview), [preview]);

    const handleFileChange = (e) => {
        const selectedFile = e.target.files[0];
        if (selectedFile) {
            setFile(selectedFile);
            if (preview) URL.revokeObjectURL(preview);
            setPreview(URL.createObjectURL(selectedFile));
            setError('');
        }
    };

    const handleClearFile = () => {
        if (preview) URL.revokeObjectURL(preview);
        setFile(null);
        setPreview('');
        if (fileInputRef.current) fileInputRef.current.value = '';
    };

    const handleTagsChange = (e) => {
        const nextTags = e.target.value;
        if (nextTags.split(',').map((tag) => tag.trim()).filter(Boolean).length <= 5) setTags(nextTags);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!file) {
            setError('Будь ласка, виберіть файл зображення.');
            return;
        }

        const normalizedTags = tags.split(',').map((tag) => tag.trim()).filter(Boolean).filter((tag, index, allTags) => allTags.findIndex((item) => item.toLowerCase() === tag.toLowerCase()) === index);
        if (normalizedTags.length > 5) {
            setError('Можна додати не більше 5 унікальних тегів.');
            return;
        }

        setLoading(true);
        setError('');

        const formData = new FormData();
        formData.append('file', file);
        if (description) formData.append('description', description);
        if (normalizedTags.length) formData.append('tags', normalizedTags.join(', '));

        try {
            await api.post('/photos/', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });

            await onUploadSuccess?.();
            onClose();
        } catch (err) {
            const detail = err.response?.data?.detail;
            setError(Array.isArray(detail) ? detail.map((item) => item.msg).join(', ') : detail || 'Помилка під час завантаження фото.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="modal-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
            <section className="upload-modal" role="dialog" aria-modal="true" aria-labelledby="upload-title">
                <div className="modal-heading"><div><p className="eyebrow">New post</p><h3 id="upload-title">Завантажити світлину</h3></div><button className="icon-button" type="button" onClick={onClose} aria-label="Закрити вікно">×</button></div>
                {error && <p className="error-message" role="alert">{error}</p>}
                <form className="upload-form" onSubmit={handleSubmit}>
                    <div className="file-picker">
                        <label htmlFor="photo-file">Файл світлини</label>
                        <input ref={fileInputRef} id="photo-file" type="file" accept="image/jpeg,image/png,image/webp" onChange={handleFileChange} required />
                        <small>JPEG, PNG або WEBP</small>
                    </div>
                    {preview && <div className="preview-box"><img src={preview} alt="Попередній перегляд обраної світлини" /><button className="clear-button" type="button" onClick={handleClearFile}>Очистити</button></div>}
                    <label className="form-field"><span>Опис світлини</span><textarea placeholder="Розкажіть щось про цей момент..." value={description} onChange={(e) => setDescription(e.target.value)} rows="3" /></label>
                    <label className="form-field"><span>Теги <small>(до 5, через кому)</small></span><input type="text" placeholder="nature, sunset, travel" value={tags} onChange={handleTagsChange} /></label>
                    <div className="modal-actions"><button className="primary-button" type="submit" disabled={loading}>{loading ? 'Завантаження...' : 'Завантажити'}</button><button className="secondary-button" type="button" onClick={onClose} disabled={loading}>Скасувати</button></div>
                </form>
            </section>
        </div>
    );
}

export default UploadPhoto;
