import { useEffect, useRef, useState } from 'react';
import api from './api';
import './AvatarUpload.css';

const MAX_SIZE_MB = 3;
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp'];

export const AvatarUpload = ({ currentAvatarUrl, userName = 'User', onAvatarUpdated }) => {
    const fileInputRef = useRef(null);
    const objectUrlRef = useRef(null); // temporary preview URL that must be released
    const [preview, setPreview] = useState(currentAvatarUrl || null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const releaseObjectUrl = () => {
        if (objectUrlRef.current) {
            URL.revokeObjectURL(objectUrlRef.current);
            objectUrlRef.current = null;
        }
    };

    useEffect(() => releaseObjectUrl, []);

    const openFilePicker = () => {
        if (!loading) fileInputRef.current?.click();
    };

    const handleFileSelect = async (event) => {
        const file = event.target.files?.[0];
        event.target.value = ''; // lets the same file be chosen again later
        if (!file) return;

        setError('');

        if (!ALLOWED_TYPES.includes(file.type)) {
            setError('Unsupported format. Choose PNG, JPG, or WEBP.');
            return;
        }
        if (file.size > MAX_SIZE_MB * 1024 * 1024) {
            setError(`File size must not exceed ${MAX_SIZE_MB} MB.`);
            return;
        }

        // Show the new picture immediately while it uploads.
        const previousPreview = preview;
        releaseObjectUrl();
        objectUrlRef.current = URL.createObjectURL(file);
        setPreview(objectUrlRef.current);

        const formData = new FormData();
        formData.append('file', file);

        setLoading(true);
        try {
            const response = await api.post('/users/me/avatar', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
            releaseObjectUrl();
            setPreview(response.data.avatar_url);
            onAvatarUpdated?.(response.data.avatar_url);
        } catch (err) {
            const detail = err.response?.data?.detail;
            setError(Array.isArray(detail) ? detail.map((item) => item.msg).join(', ') : detail || 'Could not upload avatar.');
            releaseObjectUrl();
            setPreview(previousPreview);
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteAvatar = async () => {
        if (!window.confirm('Remove your avatar?')) return;
        setLoading(true);
        setError('');
        try {
            await api.delete('/users/me/avatar');
            releaseObjectUrl();
            setPreview(null);
            onAvatarUpdated?.(null);
        } catch (err) {
            setError(err.response?.data?.detail || 'Could not remove avatar.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="av-root">
            {/* The picture itself is the "change photo" control. */}
            <button className="av-avatar" type="button" onClick={openFilePicker} disabled={loading} aria-label={preview ? 'Change profile photo' : 'Upload profile photo'}>
                {preview ? <img src={preview} alt={`${userName}'s avatar`} /> : <span aria-hidden="true">{userName.charAt(0).toUpperCase()}</span>}
                <span className={loading ? 'av-overlay is-visible' : 'av-overlay'} aria-hidden="true">
                    {loading ? 'Uploading...' : preview ? 'Change photo' : 'Add photo'}
                </span>
            </button>

            <input
                ref={fileInputRef}
                className="visually-hidden"
                type="file"
                accept={ALLOWED_TYPES.join(',')}
                onChange={handleFileSelect}
                tabIndex={-1}
                aria-hidden="true"
            />

            {preview ? (
                <button className="btn btn-secondary av-remove" type="button" onClick={handleDeleteAvatar} disabled={loading}>
                    Delete Profile Photo
                </button>
            ) : (
                <p className="av-hint">Click the circle to add a photo</p>
            )}

            {error && <p className="av-error" role="alert">{error}</p>}
        </div>
    );
};
