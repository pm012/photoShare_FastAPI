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
            setError('Please choose an image file.');
            return;
        }

        const normalizedTags = tags.split(',').map((tag) => tag.trim()).filter(Boolean).filter((tag, index, allTags) => allTags.findIndex((item) => item.toLowerCase() === tag.toLowerCase()) === index);
        if (normalizedTags.length > 5) {
            setError('You can add up to 5 unique tags.');
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
        <div className="modal-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
            <section className="upload-modal" role="dialog" aria-modal="true" aria-labelledby="upload-title">
                <div className="modal-heading"><div><p className="eyebrow">New post</p><h3 id="upload-title">Upload a photo</h3></div><button className="icon-button" type="button" onClick={onClose} aria-label="Close dialog">×</button></div>
                {error && <p className="error-message" role="alert">{error}</p>}
                <form className="upload-form" onSubmit={handleSubmit}>
                    <div className="file-picker">
                        <label htmlFor="photo-file">Photo file</label>
                        <input ref={fileInputRef} id="photo-file" type="file" accept="image/jpeg,image/png,image/webp" onChange={handleFileChange} required />
                        <small>JPEG, PNG, or WEBP</small>
                    </div>
                    {preview && <div className="preview-box"><img src={preview} alt="Preview of selected photo" /><button className="clear-button" type="button" onClick={handleClearFile}>Clear</button></div>}
                    <label className="form-field"><span>Photo description</span><textarea placeholder="Tell us about this moment..." value={description} onChange={(e) => setDescription(e.target.value)} rows="3" /></label>
                    <label className="form-field"><span>Tags <small>(up to 5, comma-separated)</small></span><input type="text" placeholder="nature, sunset, travel" value={tags} onChange={handleTagsChange} /></label>
                    <div className="modal-actions"><button className="primary-button" type="submit" disabled={loading}>{loading ? 'Uploading...' : 'Upload'}</button><button className="secondary-button" type="button" onClick={onClose} disabled={loading}>Cancel</button></div>
                </form>
            </section>
        </div>
    );
}

export default UploadPhoto;
