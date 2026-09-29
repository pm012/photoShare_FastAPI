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
            setError(errorMessage(err, 'Не вдалося виконати пошук користувачів.'));
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
            setMessage('Зміни збережено.');
        } catch (err) {
            setError(errorMessage(err, 'Не вдалося змінити дані користувача.'));
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
        if (user.id === currentUser?.id || !window.confirm(`Видалити акаунт @${user.username}?`)) return;
        updateUser(user.id, () => api.delete(`/users/${user.id}`));
    };

    const isAdmin = currentRole === 'admin' || roleName(currentUser?.role) === 'admin';
    const hasManagementAccess = ['admin', 'moderator'].includes(currentRole || roleName(currentUser?.role));

    if (currentUser && !hasManagementAccess) return <main className="admin-page"><p className="error-message" role="alert">Цей розділ доступний лише модераторам та адміністраторам.</p></main>;

    return (
        <main className="admin-page">
            <header className="admin-heading"><div><p className="eyebrow">Control room</p><h2>Керування користувачами</h2><p>Пошук за username або email і контроль доступу до платформи.</p></div><span className="role-badge">{isAdmin ? 'Адміністратор' : 'Модератор'}</span></header>
            <form className="admin-search" onSubmit={(event) => loadUsers(event, 1, query)}><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Наприклад: olena або email@example.com" aria-label="Пошук користувача" /><button className="primary-button" disabled={loading}>{loading ? 'Шукаємо...' : 'Знайти'}</button></form>
            {error && <p className="error-message" role="alert">{error}</p>}
            {message && <p className="success-message" role="status">{message}</p>}
            <section className="user-table-section"><div className="section-heading"><div><p className="eyebrow">Accounts</p><h3>Результати пошуку</h3></div><span>Сторінка {page}</span></div>{users.length === 0 ? <div className="feed-status">Користувачів не знайдено.</div> : <div className="user-table-wrap"><table className="user-table"><thead><tr><th>Користувач</th><th>Роль</th><th>Статус</th><th>Реєстрація</th><th>Дії</th></tr></thead><tbody>{users.map((user) => { const isSelf = user.id === currentUser?.id; const isWorking = workingId === user.id; return <tr key={user.id}><td><strong>@{user.username}</strong><small>{user.email}</small></td><td>{isAdmin && !isSelf ? <select value={roleName(user.role)} onChange={(event) => handleRoleChange(user, event.target.value)} disabled={isWorking}><option value="user">Користувач</option><option value="moderator">Модератор</option><option value="admin">Адміністратор</option></select> : <span className="table-role">{roleName(user.role)}</span>}</td><td><span className={user.is_active ? 'account-status active' : 'account-status'}>{user.is_active ? 'Активний' : 'Заблокований'}</span></td><td>{new Date(user.created_at).toLocaleDateString('uk-UA')}</td><td><div className="table-actions"><button className="secondary-button" onClick={() => handleBanToggle(user)} disabled={!isAdmin || isSelf || isWorking}>{user.is_active ? 'Заблокувати' : 'Розблокувати'}</button>{isAdmin && <button className="danger-button" onClick={() => handleDelete(user)} disabled={isSelf || isWorking}>Видалити</button>}</div></td></tr>; })}</tbody></table></div>}<div className="pagination-controls"><button className="secondary-button" onClick={() => loadUsers(undefined, page - 1)} disabled={loading || page === 1}>← Попередня</button><span>Сторінка {page}</span><button className="secondary-button" onClick={() => loadUsers(undefined, page + 1)} disabled={loading || !hasNextPage}>Наступна →</button></div></section>
        </main>
    );
}

export default AdminPanel;
