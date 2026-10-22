import { useEffect, useState } from 'react';
import api from './api';
import UserAvatar from './UserAvatar';
import './AdminPanel.css';

const PAGE_SIZE = 20;

const roleName = (role) => {
    if (!role) return '';
    const normalizedRole = String(role).trim().toLowerCase();
    return normalizedRole.includes('.') ? normalizedRole.split('.').pop() : normalizedRole;
};
const roleLabel = (role) => {
    const name = roleName(role);
    return name.charAt(0).toUpperCase() + name.slice(1);
};
const errorMessage = (error, fallback) => {
    const detail = error.response?.data?.detail;
    return Array.isArray(detail) ? detail.map((item) => item.msg).join(', ') : detail || fallback;
};
const formatDate = (date) => new Date(date).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });

function AdminPanel({ currentRole }) {
    const [query, setQuery] = useState('');               // text currently in the search box
    const [appliedQuery, setAppliedQuery] = useState(''); // search that was actually submitted
    const [users, setUsers] = useState([]);
    const [currentUser, setCurrentUser] = useState(null);
    const [page, setPage] = useState(1);
    const [hasNextPage, setHasNextPage] = useState(false);
    const [reloadKey, setReloadKey] = useState(0);
    const [loading, setLoading] = useState(true);
    const [workingId, setWorkingId] = useState(null);
    const [error, setError] = useState('');
    const [message, setMessage] = useState('');

    // Who is using the panel (loaded once).
    useEffect(() => {
        let ignore = false;
        api.get('/users/me')
            .then((response) => { if (!ignore) setCurrentUser(response.data); })
            .catch((err) => { if (!ignore) setError(errorMessage(err, 'Could not load your profile.')); });
        return () => { ignore = true; };
    }, []);

    // Load users whenever the submitted search or the page changes.
    useEffect(() => {
        let ignore = false;
        const request = window.setTimeout(async () => {
            setLoading(true);
            setError('');
            try {
                const response = await api.get('/search/users', { params: { query: appliedQuery || undefined, page, page_size: PAGE_SIZE } });
                if (ignore) return;
                setUsers(response.data);
                setHasNextPage(response.data.length === PAGE_SIZE);
            } catch (err) {
                if (!ignore) setError(errorMessage(err, 'Could not search users.'));
            } finally {
                if (!ignore) setLoading(false);
            }
        }, 0);
        return () => {
            ignore = true;
            window.clearTimeout(request);
        };
    }, [appliedQuery, page, reloadKey]);

    // Success messages disappear on their own.
    useEffect(() => {
        if (!message) return undefined;
        const timer = window.setTimeout(() => setMessage(''), 4000);
        return () => window.clearTimeout(timer);
    }, [message]);

    const handleSearch = (event) => {
        event.preventDefault();
        setMessage('');
        setAppliedQuery(query.trim());
        setPage(1);
        setReloadKey((key) => key + 1);
    };

    const handleClear = () => {
        setQuery('');
        setAppliedQuery('');
        setPage(1);
    };

    const updateUser = async (userId, action) => {
        try {
            setWorkingId(userId);
            setError('');
            setMessage('');
            const response = await action();
            if (response?.data) setUsers((items) => items.map((user) => user.id === userId ? response.data : user));
            if (response?.status === 204) setUsers((items) => items.filter((user) => user.id !== userId));
            setMessage('Changes are saved.');
        } catch (err) {
            setError(errorMessage(err, 'Could not update user details.'));
        } finally {
            setWorkingId(null);
        }
    };

    const handleRoleChange = (user, role) => {
        if (role === roleName(user.role) || user.id === currentUser?.id) return;
        updateUser(user.id, () => api.patch(`/users/${user.id}/role`, { role }));
    };

    const handleBanToggle = (user) => {
        if (user.id === currentUser?.id) return;
        const nextActive = !user.is_active;
        updateUser(user.id, () => api.patch(`/users/${user.id}/ban`, null, { params: { is_active: nextActive } }));
    };

    const handleDelete = (user) => {
        if (user.id === currentUser?.id || !window.confirm(`Delete the account @${user.username}?`)) return;
        updateUser(user.id, () => api.delete(`/users/${user.id}`));
    };

    const isAdmin = currentRole === 'admin' || roleName(currentUser?.role) === 'admin';
    const hasManagementAccess = ['admin', 'moderator'].includes(currentRole || roleName(currentUser?.role));

    if (currentUser && !hasManagementAccess) return <main className="admin-page"><p className="error-message" role="alert">This section is available to moderators and administrators only.</p></main>;

    return (
        <main className="admin-page">
            <header className="ad-header">
                <div>
                    <h2>Users Management</h2>
                    <p>Search by username or email and manage platform access.</p>
                </div>
                <span className="ad-badge">{isAdmin ? 'Administrator' : 'Moderator'}</span>
            </header>

            <form className="ad-search" role="search" onSubmit={handleSearch}>
                <input className="field" type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search by username or email" aria-label="Search users" />
                <button className="btn btn-primary" type="submit" disabled={loading}>{loading ? 'Searching...' : 'Search'}</button>
                {appliedQuery && <button className="btn btn-secondary" type="button" onClick={handleClear} disabled={loading}>Clear</button>}
            </form>

            {error && <p className="error-message" role="alert">{error}</p>}
            {message && <p className="success-message" role="status">{message}</p>}

            <section>
                <div className="ad-section-header">
                    <h3>{appliedQuery ? `Results for "${appliedQuery}"` : 'All users'}</h3>
                    <span>{users.length} on this page</span>
                </div>

                {!loading && users.length === 0 ? (
                    <div className="feed-status">No users found.</div>
                ) : (
                    <div className="ad-table-wrap" aria-busy={loading}>
                        <table className="ad-table">
                            <thead>
                                <tr>
                                    <th scope="col">User</th>
                                    <th scope="col">Role</th>
                                    <th scope="col">Status</th>
                                    <th scope="col">Joined</th>
                                    <th scope="col">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {users.map((user) => {
                                    const isSelf = user.id === currentUser?.id;
                                    const isWorking = workingId === user.id;
                                    return (
                                        <tr key={user.id}>
                                            <td>
                                                <div className="ad-user">
                                                    <UserAvatar username={user.username} url={user.avatar_url} size={36} />
                                                    <div className="ad-user__text"><strong>@{user.username}</strong><span>{user.email}</span></div>
                                                </div>
                                            </td>
                                            <td>
                                                {isAdmin && !isSelf ? (
                                                    <select className="field ad-role-select" aria-label={`Role of ${user.username}`} value={roleName(user.role)} onChange={(event) => handleRoleChange(user, event.target.value)} disabled={isWorking}>
                                                        <option value="user">User</option>
                                                        <option value="moderator">Moderator</option>
                                                        <option value="admin">Administrator</option>
                                                    </select>
                                                ) : (
                                                    <span className="ad-role">{roleLabel(user.role)}</span>
                                                )}
                                            </td>
                                            <td><span className={user.is_active ? 'ad-status is-active' : 'ad-status'}>{user.is_active ? 'Active' : 'Banned'}</span></td>
                                            <td>{formatDate(user.created_at)}</td>
                                            <td>
                                                <div className="ad-actions">
                                                    <button
                                                        className="btn btn-secondary"
                                                        type="button"
                                                        onClick={() => handleBanToggle(user)}
                                                        disabled={!isAdmin || isSelf || isWorking}
                                                        title={!isAdmin ? 'Only administrators can ban users' : isSelf ? "You can't ban your own account" : undefined}
                                                    >
                                                        {user.is_active ? 'Ban' : 'Unban'}
                                                    </button>
                                                    {isAdmin && (
                                                        <button
                                                            className="btn btn-secondary ad-btn-danger"
                                                            type="button"
                                                            onClick={() => handleDelete(user)}
                                                            disabled={isSelf || isWorking}
                                                            title={isSelf ? "You can't delete your own account" : undefined}
                                                        >
                                                            Delete
                                                        </button>
                                                    )}
                                                </div>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                )}

                <nav className="ad-pagination" aria-label="Pagination">
                    <button className="btn btn-secondary" type="button" onClick={() => setPage((current) => current - 1)} disabled={loading || page === 1}>‹ Previous</button>
                    <span>Page {page}</span>
                    <button className="btn btn-secondary" type="button" onClick={() => setPage((current) => current + 1)} disabled={loading || !hasNextPage}>Next ›</button>
                </nav>
            </section>
        </main>
    );
}

export default AdminPanel;