import { useEffect, useRef, useState } from 'react';
import api from './api';
import './UploadPhoto.css';

const MAX_TAGS = 5;
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp', "image/jpg"];


const formatSize = (bytes) => (bytes >= 1024 * 1024 ? `${(bytes / (1024 * 1024)).toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`);

// "a, b, A" -> ["a", "b"] (trimmed, empty and duplicate tags removed)
const parseTags = (value) => value
    .split(',')
    .map((tag) => tag.trim())
    .filter(Boolean)
    .filter((tag, index, allTags) => allTags.findIndex((item) => item.toLowerCase() === tag.toLowerCase()) === index);

function UploadPhoto({ onUploadSuccess, onClose }) {
    const [file, setFile] = useState(null);
    const [preview, setPreview] = useState('');
    const [description, setDescription] = useState('');
    const [tags, setTags] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [isDragging, setIsDragging] = useState(false);
    const fileInputRef = useRef(null);

    const normalizedTags = parseTags(tags);
    const tooManyTags = normalizedTags.length > MAX_TAGS;

    // Free the temporary preview URL when it changes or the dialog closes.
    useEffect(() => () => preview && URL.revokeObjectURL(preview), [preview]);

    const selectFile = (selectedFile) => {
        if (!selectedFile) return;
        if (!ALLOWED_TYPES.includes(selectedFile.type)) {
            setError('Only JPEG, PNG, or WEBP images are supported.');
            return;
        }
        setFile(selectedFile);
        setPreview(URL.createObjectURL(selectedFile));
        setError('');
    };

    const handleFileChange = (e) => {
        selectFile(e.target.files[0]);
        e.target.value = ''; // lets the same file be picked again after removing it
    };

    const handleDrop = (e) => {
        e.preventDefault();
        setIsDragging(false);
        selectFile(e.dataTransfer.files[0]);
    };

    const handleClearFile = () => {
        setFile(null);
        setPreview('');
    };

    // Ignore close requests while an upload is in progress.
    const handleClose = () => {
        if (!loading) onClose();
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!file) {
            setError('Please choose an image file.');
            return;
        }
        if (tooManyTags) {
            setError(`You can add up to ${MAX_TAGS} unique tags.`);
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
            setError(Array.isArray(detail) ? detail.map((item) => item.msg).join(', ') : detail || 'Could not upload photo.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="modal-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && handleClose()}>
            <section className="upload-modal" role="dialog" aria-modal="true" aria-labelledby="upload-title">
                <div className="modal-heading">
                    <h3 id="upload-title">Upload a photo</h3>
                    <button className="icon-button" type="button" onClick={handleClose} aria-label="Close dialog">×</button>
                </div>

                {error && <p className="error-message" role="alert">{error}</p>}

                <form className="upload-form" onSubmit={handleSubmit}>
                    <input ref={fileInputRef} id="photo-file" className="visually-hidden" type="file" accept={ALLOWED_TYPES.join(',')} onChange={handleFileChange} />

                    {file ? (
                        <div className="upload-file">
                            <img src={preview} alt="Preview of selected photo" />
                            <div className="upload-file__bar">
                                <div className="upload-file__info">
                                    <span className="upload-file__name">{file.name}</span>
                                    <span className="upload-file__size">{formatSize(file.size)}</span>
                                </div>
                                <button className="btn btn-secondary" type="button" onClick={() => fileInputRef.current?.click()} disabled={loading}>Replace</button>
                                <button className="btn btn-secondary" type="button" onClick={handleClearFile} disabled={loading}>Remove</button>
                            </div>
                        </div>
                    ) : (
                        <label
                            htmlFor="photo-file"
                            className={isDragging ? 'dropzone is-dragging' : 'dropzone'}
                            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                            onDragLeave={() => setIsDragging(false)}
                            onDrop={handleDrop}
                        >
                            <span className="dropzone__title">Drag a photo here or <u>browse</u></span>
                            <small>JPEG, PNG, or WEBP</small>
                        </label>
                    )}

                    <label className="upload-field">
                        <span className="upload-field__label">Description</span>
                        <textarea className="field" placeholder="Tell us about this moment..." value={description} onChange={(e) => setDescription(e.target.value)} rows="3" />
                    </label>

                    <label className="upload-field">
                        <span className="upload-field__label">Tags</span>
                        <input className="field" type="text" placeholder="nature, sunset, travel" autoComplete="off" value={tags} onChange={(e) => setTags(e.target.value)} aria-invalid={tooManyTags} />
                        <span className={tooManyTags ? 'upload-field__hint is-error' : 'upload-field__hint'}>
                            <span>{tooManyTags ? `Remove ${normalizedTags.length - MAX_TAGS} tag(s) to continue` : 'Separate tags with commas'}</span>
                            <span>{normalizedTags.length}/{MAX_TAGS}</span>
                        </span>
                    </label>

                    <div className="modal-actions">
                        <button className="btn btn-secondary" type="button" onClick={handleClose} disabled={loading}>Cancel</button>
                        <button className="btn btn-primary" type="submit" disabled={loading || tooManyTags}>{loading ? 'Uploading...' : 'Upload'}</button>
                    </div>
                </form>
            </section>
        </div>
    );
}

export default UploadPhoto;