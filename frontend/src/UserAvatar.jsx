import { useState } from 'react';
import './UserAvatar.css';

// Round avatar: the user's picture when available, otherwise their initial.
// Also falls back to the initial if the picture fails to load.
function UserAvatar({ username = '', url, size = 32 }) {
    const [failedUrl, setFailedUrl] = useState(null);
    const showImage = Boolean(url) && failedUrl !== url;

    return (
        <span className="ua-avatar" style={{ '--ua-size': `${size}px` }} aria-hidden="true">
            {showImage
                ? <img src={url} alt="" loading="lazy" onError={() => setFailedUrl(url)} />
                : (username.charAt(0) || '?').toUpperCase()}
        </span>
    );
}

export default UserAvatar;
