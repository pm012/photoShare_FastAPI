import { useCallback, useEffect, useState } from 'react';
import api from './api';
import UserAvatar from './UserAvatar';
import './PhotoPage.css';

const STAFF_ROLES = ['admin', 'moderator'];
const MAX_TAGS = 5;

// "a, b, A" -> ["a", "b"] (trimmed, empty and duplicate tags removed)
const parseTags = (value) => value
    .split(',')
    .map((tag) => tag.trim())
    .filter(Boolean)
    .filter((tag, index, allTags) => allTags.findIndex((item) => item.toLowerCase() === tag.toLowerCase()) === index);
const tagsToText = (tags) => (tags || []).map((tag) => tag.name).join(', ');

// Same normalisation as in App.jsx ("UserRole.ADMIN" -> "admin").
const normalizeRole = (role) => {
    const value = String(role || '').toLowerCase();
    return value.includes('.') ? value.split('.').pop() : value;
};

const getErrorMessage = (error, fallback) => {
    const detail = error.response?.data?.detail;
    return Array.isArray(detail) ? detail.map((item) => item.msg).join(', ') : detail || fallback;
};

function PhotoPage({ photoId, onBack, onProfileSelect }) {
    const [photo, setPhoto] = useState(null);
    const [currentUser, setCurrentUser] = useState(null);
    const [comments, setComments] = useState([]);
    const [rating, setRating] = useState(null);
    const [myRating, setMyRating] = useState(0);       // the stars the user has given (stays visible after clicking)
    const [hoverRating, setHoverRating] = useState(0); // preview while hovering / focusing a star
    const [commentText, setCommentText] = useState('');
    const [editingCommentId, setEditingCommentId] = useState(null);
    const [editingText, setEditingText] = useState('');
    const [description, setDescription] = useState('');
    const [tagsText, setTagsText] = useState('');
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
            const [userResponse, commentsResponse, ratingResponse, ratingsResponse] = await Promise.all([
                api.get('/users/me'),
                api.get(`/photos/${photoId}/comments`),
                api.get(`/photos/${photoId}/rate/summary`),
                // The page must still open if this list is not available for the current user.
                api.get(`/photos/${photoId}/ratings`).catch(() => ({ data: [] })),
            ]);
            setPhoto(photoResponse.data);
            setDescription(photoResponse.data.description || '');
            setTagsText(tagsToText(photoResponse.data.tags));
            setCurrentUser(userResponse.data);
            setComments(commentsResponse.data);
            setRating(ratingResponse.data);
            setMyRating(ratingsResponse.data.find((item) => item.user_id === userResponse.data.id)?.rate || 0);
        } catch (err) {
            setError(getErrorMessage(err, 'Could not load the photo.'));
        } finally {
            setLoading(false);
        }
    }, [photoId]);

    useEffect(() => {
        const request = window.setTimeout(loadPhoto, 0);
        return () => window.clearTimeout(request);
    }, [loadPhoto]);

    // Success messages disappear on their own.
    useEffect(() => {
        if (!actionMessage) return undefined;
        const timer = window.setTimeout(() => setActionMessage(''), 4000);
        return () => window.clearTimeout(timer);
    }, [actionMessage]);

    const runAction = async (action, successMessage) => {
        try {
            setSubmitting(true);
            setError('');
            setActionMessage('');
            await action();
            setActionMessage(successMessage);
        } catch (err) {
            setError(getErrorMessage(err, 'Could not complete the action.'));
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
        }, 'Comment added.');
    };

    const handleCommentUpdate = async (commentId) => {
        if (!editingText.trim()) return;
        await runAction(async () => {
            const response = await api.put(`/photos/comments/${commentId}`, { text: editingText.trim() });
            setComments((items) => items.map((comment) => comment.id === commentId ? response.data : comment));
            setEditingCommentId(null);
        }, 'Comment updated.');
    };

    const handleCommentDelete = async (commentId) => {
        if (!window.confirm('Delete this comment?')) return;
        await runAction(async () => {
            await api.delete(`/photos/comments/${commentId}`);
            setComments((items) => items.filter((comment) => comment.id !== commentId));
        }, 'Comment deleted.');
    };

    // FIX: the old code called setSelectedRating(0) after saving, which cleared the stars right away.
    // Now the chosen value is kept in `myRating`, so the stars stay filled.
    const handleRating = async (value) => {
        if (!value || photo.user_id === currentUser.id) return;
        await runAction(async () => {
            await api.post(`/photos/${photoId}/rate`, { rate: value });
            setMyRating(value);
            const response = await api.get(`/photos/${photoId}/rate/summary`);
            setRating(response.data);
        }, `You rated this photo ${value} out of 5.`);
    };

    const handleDetailsSave = async () => {
        const tags = parseTags(tagsText);
        if (tags.length > MAX_TAGS) {
            setError(`You can add up to ${MAX_TAGS} unique tags.`);
            return;
        }
        await runAction(async () => {
            const response = await api.put(`/photos/${photoId}`, { description, tags });
            setPhoto((current) => ({ ...current, description: response.data.description, tags: response.data.tags }));
            setTagsText(tagsToText(response.data.tags));
            setIsEditingDescription(false);
        }, 'Photo details updated.');
    };

    const cancelDetailsEdit = () => {
        setDescription(photo.description || '');
        setTagsText(tagsToText(photo.tags));
        setIsEditingDescription(false);
    };

    const handleDeletePhoto = async () => {
        if (!window.confirm('Delete this photo? This action cannot be undone.')) return;
        await runAction(async () => {
            await api.delete(`/photos/${photoId}`);
            onBack();
        }, 'Photo deleted.');
    };

    const handleTransform = async (event) => {
        event.preventDefault();
        await runAction(async () => {
            const response = await api.post(`/photos/${photoId}/transform`, { preset });
            setTransformation(response.data);
        }, 'Transformed photo created.');
    };

    const backButton = <button className="btn btn-secondary pd-back" type="button" onClick={onBack}>← Back to feed</button>;

    if (loading) return <main className="photo-page"><div className="feed-status" role="status">Loading photo...</div></main>;
    if (error && !photo) return <main className="photo-page">{backButton}<p className="error-message" role="alert">{error}</p></main>;

    const isStaff = STAFF_ROLES.includes(normalizeRole(currentUser.role));
    const isOwner = currentUser.id === photo.user_id;
    const isAdmin = normalizeRole(currentUser.role) === 'admin';
    // The backend lets only the owner or an administrator edit or delete a photo.
    const canManagePhoto = isOwner || isAdmin;
    const parsedTags = parseTags(tagsText);
    const tooManyTags = parsedTags.length > MAX_TAGS;
    const canRate = !isOwner;
    // The API does not return usernames for photos/comments yet, so for the current user's own content use /users/me.
    const authorName = photo.username || (isOwner ? currentUser.username : null);
    const getCommentAuthor = (comment) => comment.username || (comment.user_id === currentUser.id ? currentUser.username : null);
    const shownRating = hoverRating || myRating;
    const averageRating = Number(rating?.average_rating || 0);
    const totalVotes = rating?.total_votes || 0;

    return (
        <main className="photo-page">
            {backButton}
            {error && <p className="error-message" role="alert">{error}</p>}
            {actionMessage && <p className="success-message" role="status">{actionMessage}</p>}

            <div className="pd-layout">
                <section className="pd-viewer">
                    <img src={photo.url} alt={photo.description || 'PhotoShare photo'} />
                </section>

                <aside className="pd-sidebar">
                    <section className="pd-card">
                        {authorName && (
                            <button className="pd-author" type="button" onClick={() => onProfileSelect?.(authorName)} aria-label={`Open profile of ${authorName}`}>
                                <UserAvatar username={authorName} url={photo.avatar_url || (isOwner ? currentUser.avatar_url : null)} size={28} />
                                <span className="pd-author__name">@{authorName}</span>
                            </button>
                        )}
                        <h2>{photo.description || 'Photo without a description'}</h2>
                        {photo.tags?.length > 0 && (
                            <div className="pd-tags">
                                {photo.tags.map((tag) => <span className="pd-tag" key={tag.id}>#{tag.name}</span>)}
                            </div>
                        )}
                    </section>

                    <section className="pd-card">
                        <h3>Rating</h3>
                        <p className="pd-score">
                            <strong>{totalVotes ? averageRating.toFixed(1) : '–'}</strong>
                            <span>{totalVotes ? `average · ${totalVotes} ${totalVotes === 1 ? 'rating' : 'ratings'}` : 'No ratings yet'}</span>
                        </p>
                        {canRate ? (
                            <>
                                <div className="pd-stars" role="group" aria-label="Your rating" onMouseLeave={() => setHoverRating(0)}>
                                    {[1, 2, 3, 4, 5].map((value) => (
                                        <button
                                            key={value}
                                            className={shownRating >= value ? 'pd-star is-active' : 'pd-star'}
                                            type="button"
                                            onClick={() => handleRating(value)}
                                            onMouseEnter={() => setHoverRating(value)}
                                            onFocus={() => setHoverRating(value)}
                                            onBlur={() => setHoverRating(0)}
                                            disabled={submitting}
                                            aria-label={`Rate ${value} out of 5`}
                                            aria-pressed={myRating === value}
                                        >★</button>
                                    ))}
                                </div>
                                <p className="pd-hint">{myRating ? `Your rating: ${myRating} out of 5` : 'Click a star to rate this photo'}</p>
                            </>
                        ) : (
                            <p className="pd-hint">You cannot rate your own photos.</p>
                        )}
                    </section>

                    {canManagePhoto && (
                        <section className="pd-card">
                            <h3>Manage photo</h3>
                            {isEditingDescription ? (
                                <>
                                    <label className="pd-field">
                                        <span className="pd-field__label">Description</span>
                                        <textarea className="field" value={description} onChange={(event) => setDescription(event.target.value)} rows="3" />
                                    </label>
                                    <label className="pd-field">
                                        <span className="pd-field__label">Tags</span>
                                        <input className="field" type="text" placeholder="nature, sunset, travel" autoComplete="off" value={tagsText} onChange={(event) => setTagsText(event.target.value)} aria-invalid={tooManyTags} />
                                        <span className={tooManyTags ? 'pd-hint is-error' : 'pd-hint'}>
                                            {tooManyTags ? `Remove ${parsedTags.length - MAX_TAGS} tag(s) to save` : 'Separate tags with commas'} · {parsedTags.length}/{MAX_TAGS}
                                        </span>
                                    </label>
                                    <div className="pd-actions">
                                        <button className="btn btn-secondary" type="button" onClick={cancelDetailsEdit} disabled={submitting}>Cancel</button>
                                        <button className="btn btn-primary" type="button" onClick={handleDetailsSave} disabled={submitting || tooManyTags}>Save</button>
                                    </div>
                                </>
                            ) : (
                                <div className="pd-actions">
                                    <button className="btn btn-secondary" type="button" onClick={() => setIsEditingDescription(true)}>Edit details</button>
                                    <button className="btn btn-danger" type="button" onClick={handleDeletePhoto} disabled={submitting}>Delete</button>
                                </div>
                            )}
                        </section>
                    )}

                    <form className="pd-card" onSubmit={handleTransform}>
                        <h3>Create a version</h3>
                        <select className="field" aria-label="Preset" value={preset} onChange={(event) => setPreset(event.target.value)}>
                            <option value="thumbnail">Thumbnail</option>
                            <option value="avatar">Avatar</option>
                            <option value="black_white">Black and white</option>
                        </select>
                        <button className="btn btn-secondary" type="submit" disabled={submitting}>Apply preset</button>
                        {transformation && (
                            <div className="pd-transformed">
                                <img src={transformation.transformed_url} alt="Transformed photo" />
                                <a href={transformation.qr_code_url} target="_blank" rel="noreferrer">View QR code</a>
                            </div>
                        )}
                    </form>
                </aside>
            </div>

            <section className="pd-comments" aria-labelledby="comments-title">
                <div className="pd-comments__header">
                    <h3 id="comments-title">Comments</h3>
                    <span className="pd-count">{comments.length}</span>
                </div>

                <form className="pd-comment-form" onSubmit={handleCommentSubmit}>
                    <textarea className="field" aria-label="Write a comment" value={commentText} onChange={(event) => setCommentText(event.target.value)} maxLength="500" placeholder="Write a comment..." rows="3" />
                    <div className="pd-form-footer">
                        <span>{commentText.length}/500</span>
                        <button className="btn btn-primary" type="submit" disabled={submitting || !commentText.trim()}>Post</button>
                    </div>
                </form>

                <div className="pd-comment-list">
                    {comments.length === 0 ? (
                        <p className="feed-status">No comments yet. Start the conversation.</p>
                    ) : comments.map((comment) => (
                        <article className="pd-comment" key={comment.id}>
                            <div className="pd-comment__meta">
                                {getCommentAuthor(comment) ? (
                                    <button className="pd-link-btn" type="button" onClick={() => onProfileSelect?.(getCommentAuthor(comment))}>@{getCommentAuthor(comment)}</button>
                                ) : (
                                    <strong>User #{comment.user_id}</strong>
                                )}
                                {' · '}{new Date(comment.created_at).toLocaleDateString('en-US')}
                            </div>
                            {editingCommentId === comment.id ? (
                                <>
                                    <textarea className="field" aria-label="Edit comment" value={editingText} onChange={(event) => setEditingText(event.target.value)} maxLength="500" rows="3" />
                                    <div className="pd-actions">
                                        <button className="btn btn-secondary" type="button" onClick={() => setEditingCommentId(null)} disabled={submitting}>Cancel</button>
                                        <button className="btn btn-primary" type="button" onClick={() => handleCommentUpdate(comment.id)} disabled={submitting || !editingText.trim()}>Save</button>
                                    </div>
                                </>
                            ) : (
                                <>
                                    <p>{comment.text}</p>
                                    {(comment.user_id === currentUser.id || isStaff) && (
                                        <div className="pd-comment__actions">
                                            <button className="pd-link-btn" type="button" onClick={() => { setEditingCommentId(comment.id); setEditingText(comment.text); }}>Edit</button>
                                            {isStaff && <button className="pd-link-btn is-danger" type="button" onClick={() => handleCommentDelete(comment.id)} disabled={submitting}>Delete</button>}
                                        </div>
                                    )}
                                </>
                            )}
                        </article>
                    ))}
                </div>
            </section>
        </main>
    );
}

export default PhotoPage;