import { useCallback, useEffect, useState } from 'react';
import api from './api';

const getErrorMessage = (error, fallback) => {
    const detail = error.response?.data?.detail;
    return Array.isArray(detail) ? detail.map((item) => item.msg).join(', ') : detail || fallback;
};

function PhotoPage({ photoId, onBack }) {
    const [photo, setPhoto] = useState(null);
    const [currentUser, setCurrentUser] = useState(null);
    const [comments, setComments] = useState([]);
    const [rating, setRating] = useState(null);
    const [commentText, setCommentText] = useState('');
    const [selectedRating, setSelectedRating] = useState(0);
    const [editingCommentId, setEditingCommentId] = useState(null);
    const [editingText, setEditingText] = useState('');
    const [description, setDescription] = useState('');
    const [isEditingDescription, setIsEditingDescription] = useState(false);
    const [preset, setPreset] = useState('thumbnail');
    const [transformation, setTransformation] = useState(null);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState('');
    const [actionMessage, setActionMessage] = useState('');

    const loadPhoto = useCallback(async () => {
        try {
            setLoading(true);
            setError('');
            const photoResponse = await api.get(`/photos/${photoId}`);
            const [userResponse, commentsResponse, ratingResponse] = await Promise.all([
                api.get('/users/me'),
                api.get(`/photos/${photoId}/comments`),
                api.get(`/photos/${photoId}/rate/summary`),
            ]);
            setPhoto(photoResponse.data);
            setDescription(photoResponse.data.description || '');
            setCurrentUser(userResponse.data);
            setComments(commentsResponse.data);
            setRating(ratingResponse.data);
        } catch (err) {
            setError(getErrorMessage(err, 'Не вдалося завантажити світлину.'));
        } finally {
            setLoading(false);
        }
    }, [photoId]);

    useEffect(() => {
        const request = window.setTimeout(loadPhoto, 0);
        return () => window.clearTimeout(request);
    }, [loadPhoto]);

    const runAction = async (action, successMessage) => {
        try {
            setSubmitting(true);
            setError('');
            setActionMessage('');
            await action();
            setActionMessage(successMessage);
        } catch (err) {
            setError(getErrorMessage(err, 'Не вдалося виконати дію.'));
        } finally {
            setSubmitting(false);
        }
    };

    const handleCommentSubmit = async (event) => {
        event.preventDefault();
        if (!commentText.trim()) return;
        await runAction(async () => {
            const response = await api.post(`/photos/${photoId}/comments`, { text: commentText.trim() });
            setComments((items) => [...items, response.data]);
            setCommentText('');
        }, 'Коментар додано.');
    };

    const handleCommentUpdate = async (commentId) => {
        if (!editingText.trim()) return;
        await runAction(async () => {
            const response = await api.put(`/photos/comments/${commentId}`, { text: editingText.trim() });
            setComments((items) => items.map((comment) => comment.id === commentId ? response.data : comment));
            setEditingCommentId(null);
        }, 'Коментар оновлено.');
    };

    const handleCommentDelete = async (commentId) => {
        if (!window.confirm('Видалити цей коментар?')) return;
        await runAction(async () => {
            await api.delete(`/photos/comments/${commentId}`);
            setComments((items) => items.filter((comment) => comment.id !== commentId));
        }, 'Коментар видалено.');
    };

    const handleRating = async (value) => {
        if (!value || photo.user_id === currentUser.id) return;
        await runAction(async () => {
            await api.post(`/photos/${photoId}/rate`, { rate: value });
            const response = await api.get(`/photos/${photoId}/rate/summary`);
            setRating(response.data);
            setSelectedRating(0);
        }, 'Дякуємо за оцінку.');
    };

    const handleDescriptionSave = async () => {
        await runAction(async () => {
            const response = await api.put(`/photos/${photoId}`, { description });
            setPhoto((current) => ({ ...current, description: response.data.description }));
            setIsEditingDescription(false);
        }, 'Опис оновлено.');
    };

    const handleDeletePhoto = async () => {
        if (!window.confirm('Видалити цю світлину? Дію неможливо скасувати.')) return;
        await runAction(async () => {
            await api.delete(`/photos/${photoId}`);
            onBack();
        }, 'Світлину видалено.');
    };

    const handleTransform = async (event) => {
        event.preventDefault();
        await runAction(async () => {
            const response = await api.post(`/photos/${photoId}/transform`, { preset });
            setTransformation(response.data);
        }, 'Трансформацію створено.');
    };

    if (loading) return <main className="photo-page"><div className="feed-status" role="status">Завантажуємо світлину...</div></main>;
    if (error && !photo) return <main className="photo-page"><button className="back-button" onClick={onBack}>← Назад до стрічки</button><p className="error-message" role="alert">{error}</p></main>;

    const canManagePhoto = currentUser.id === photo.user_id || ['admin', 'moderator'].includes(String(currentUser.role).toLowerCase());
    const canRate = currentUser.id !== photo.user_id;
    const canDeleteComments = ['admin', 'moderator'].includes(String(currentUser.role).toLowerCase());

    return (
        <main className="photo-page">
            <button className="back-button" onClick={onBack}>← Назад до стрічки</button>
            {error && <p className="error-message" role="alert">{error}</p>}
            {actionMessage && <p className="success-message" role="status">{actionMessage}</p>}
            <div className="photo-layout">
                <section className="photo-viewer"><img src={photo.url} alt={photo.description || 'Світлина PhotoShare'} /></section>
                <aside className="photo-sidebar">
                    <div className="photo-meta"><p className="eyebrow">Photo detail</p><h2>{photo.description || 'Світлина без опису'}</h2><div className="tag-list">{photo.tags?.map((tag) => <span className="tag" key={tag.id}>#{tag.name}</span>)}</div></div>
                    <div className="rating-panel"><div><strong>{rating?.average_rating?.toFixed(1) || '0.0'}</strong><span> СЕРЕДНІЙ РЕЙТИНГ · {rating?.total_votes || 0} оцінок</span></div><div className="star-picker" aria-label="Оцінити світлину">{[1, 2, 3, 4, 5].map((value) => <button key={value} className={selectedRating >= value ? 'star selected' : 'star'} onClick={() => handleRating(value)} disabled={!canRate || submitting} aria-label={`${value} зірок`}>★</button>)}</div>{!canRate && <small>Власні світлини не можна оцінювати.</small>}</div>
                    {canManagePhoto && <section className="manage-panel"><h3>Керування світлиною</h3>{isEditingDescription ? <div className="inline-edit"><textarea value={description} onChange={(event) => setDescription(event.target.value)} rows="3" /><div><button className="primary-button" onClick={handleDescriptionSave} disabled={submitting}>Зберегти</button><button className="secondary-button" onClick={() => setIsEditingDescription(false)}>Скасувати</button></div></div> : <div className="manage-actions"><button className="secondary-button" onClick={() => setIsEditingDescription(true)}>Редагувати опис</button><button className="danger-button" onClick={handleDeletePhoto} disabled={submitting}>Видалити</button></div>}</section>}
                    <form className="transform-panel" onSubmit={handleTransform}><h3>Створити версію</h3><select value={preset} onChange={(event) => setPreset(event.target.value)}><option value="thumbnail">Мініатюра</option><option value="avatar">Аватар</option><option value="black_white">Чорно-біле</option></select><button className="secondary-button" disabled={submitting}>Застосувати пресет</button>{transformation && <div className="transformation-result"><img src={transformation.transformed_url} alt="Трансформована версія" /><a href={transformation.qr_code_url} target="_blank" rel="noreferrer">Відкрити QR-код</a></div>}</form>
                </aside>
            </div>
            <section className="comments-section"><div className="section-heading"><div><p className="eyebrow">Community</p><h3>Коментарі</h3></div><span>{comments.length}</span></div><form className="comment-form" onSubmit={handleCommentSubmit}><textarea value={commentText} onChange={(event) => setCommentText(event.target.value)} maxLength="500" placeholder="Залиште коментар..." rows="3" /><div><small>{commentText.length}/500</small><button className="primary-button" disabled={submitting || !commentText.trim()}>Опублікувати</button></div></form><div className="comment-list">{comments.length === 0 ? <p className="feed-status">Коментарів ще немає.</p> : comments.map((comment) => <article className="comment-item" key={comment.id}><div className="comment-avatar">{String(comment.user_id).slice(0, 1)}</div><div className="comment-content">{editingCommentId === comment.id ? <><textarea value={editingText} onChange={(event) => setEditingText(event.target.value)} maxLength="500" /><div><button className="primary-button" onClick={() => handleCommentUpdate(comment.id)} disabled={submitting}>Зберегти</button><button className="secondary-button" onClick={() => setEditingCommentId(null)}>Скасувати</button></div></> : <><p>{comment.text}</p><small>Користувач #{comment.user_id} · {new Date(comment.created_at).toLocaleDateString('uk-UA')}</small><div className="comment-actions">{(comment.user_id === currentUser.id || ['admin', 'moderator'].includes(String(currentUser.role).toLowerCase())) && <button onClick={() => { setEditingCommentId(comment.id); setEditingText(comment.text); }}>Редагувати</button>}{canDeleteComments && <button onClick={() => handleCommentDelete(comment.id)} disabled={submitting}>Видалити</button>}</div></>}</div></article>)}</div></section>
        </main>
    );
}

export default PhotoPage;
