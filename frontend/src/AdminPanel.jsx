import { useCallback, useEffect, useState } from 'react';
import api from './api';

const roleName = (role) => {
    if (!role) return '';
    const normalizedRole = String(role).trim().toLowerCase();
    return normalizedRole.includes('.') ? normalizedRole.split('.').pop() : normalizedRole;
};
const errorMessage = (error, fallback) => error.response?.data?.detail || fallback;

function AdminPanel({ currentRole }) {
    const [query, setQuery] = useState('');
    const [users, setUsers] = useState([]);
    const [currentUser, setCurrentUser] = useState(null);
    const [page, setPage] = useState(1);
    const [hasNextPage, setHasNextPage] = useState(false);
    const [loading, setLoading] = useState(false);
    const [workingId, setWorkingId] = useState(null);
    const [error, setError] = useState('');
    const [message, setMessage] = useState('');

    const loadUsers = useCallback(async (event, requestedPage = 1, searchValue = '') => {
        event?.preventDefault();
        const search = searchValue.trim();
        try {
            setLoading(true);
            setError('');
            setMessage('');
            const [profileResponse, usersResponse] = await Promise.all([
                api.get('/users/me'),
                api.get('/search/users', { params: { query: search || undefined, page: requestedPage, page_size: 20 } }),
            ]);
            setCurrentUser(profileResponse.data);
            setUsers(usersResponse.data);
            setPage(requestedPage);
            setHasNextPage(usersResponse.data.length === 20);
        } catch (err) {
            setError(errorMessage(err, 'Could not search users.'));
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        const request = window.setTimeout(() => loadUsers(undefined, 1, ''), 0);
        return () => window.clearTimeout(request);
    }, [loadUsers]);

    const updateUser = async (userId, action) => {
        try {
            setWorkingId(userId);
            setError('');
            setMessage('');
            const response = await action();
            if (response?.data) setUsers((items) => items.map((user) => user.id === userId ? response.data : user));
            if (response?.status === 204) setUsers((items) => items.filter((user) => user.id !== userId));
            setMessage('Changes saved.');
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
            <header className="admin-heading"><div><p className="eyebrow">Control room</p><h2>User management</h2><p>Search by username or email and manage platform access.</p></div><span className="role-badge">{isAdmin ? 'Administrator' : 'Moderator'}</span></header>
            <form className="admin-search" onSubmit={(event) => loadUsers(event, 1, query)}><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="For example: olena or email@example.com" aria-label="Search users" /><button className="primary-button" disabled={loading}>{loading ? 'Searching...' : 'Search'}</button></form>
            {error && <p className="error-message" role="alert">{error}</p>}
            {message && <p className="success-message" role="status">{message}</p>}
            <section className="user-table-section"><div className="section-heading"><div><p className="eyebrow">Accounts</p><h3>Search results</h3></div><span>Page {page}</span></div>{users.length === 0 ? <div className="feed-status">No users found.</div> : <div className="user-table-wrap"><table className="user-table"><thead><tr><th>User</th><th>Role</th><th>Status</th><th>Joined</th><th>Actions</th></tr></thead><tbody>{users.map((user) => { const isSelf = user.id === currentUser?.id; const isWorking = workingId === user.id; return <tr key={user.id}><td><strong>@{user.username}</strong><small>{user.email}</small></td><td>{isAdmin && !isSelf ? <select value={roleName(user.role)} onChange={(event) => handleRoleChange(user, event.target.value)} disabled={isWorking}><option value="user">User</option><option value="moderator">Moderator</option><option value="admin">Administrator</option></select> : <span className="table-role">{roleName(user.role)}</span>}</td><td><span className={user.is_active ? 'account-status active' : 'account-status'}>{user.is_active ? 'Active' : 'Banned'}</span></td><td>{new Date(user.created_at).toLocaleDateString('en-US')}</td><td><div className="table-actions"><button className="secondary-button" onClick={() => handleBanToggle(user)} disabled={!isAdmin || isSelf || isWorking}>{user.is_active ? 'Ban' : 'Unban'}</button>{isAdmin && <button className="danger-button" onClick={() => handleDelete(user)} disabled={isSelf || isWorking}>Delete</button>}</div></td></tr>; })}</tbody></table></div>}<div className="pagination-controls"><button className="secondary-button" onClick={() => loadUsers(undefined, page - 1)} disabled={loading || page === 1}>← Previous</button><span>Page {page}</span><button className="secondary-button" onClick={() => loadUsers(undefined, page + 1)} disabled={loading || !hasNextPage}>Next →</button></div></section>
        </main>
    );
}

export default AdminPanel;
