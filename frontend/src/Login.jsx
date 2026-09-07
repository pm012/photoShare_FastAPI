import { useState } from 'react';
import api from './api';

function Login({ onLoginSuccess }) {
    // Створюємо пам'ять (стан) для полів вводу
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [username, setUsername] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [isSignup, setIsSignup] = useState(false);
    const [isForgotPassword, setIsForgotPassword] = useState(false);
    const [resetToken, setResetToken] = useState(() => new URLSearchParams(window.location.search).get('reset_token') || '');
    const [loading, setLoading] = useState(false);
    const [successMessage, setSuccessMessage] = useState('');
    const [error, setError] = useState('');

    const isResetPassword = Boolean(resetToken);

    const getErrorMessage = (err) => {
        const detail = err.response?.data?.detail;
        if (Array.isArray(detail)) {
            return detail.map((item) => item.msg).join(' ');
        }
        return detail || 'Щось пішло не так. Спробуйте пізніше.';
    };

    const switchMode = (mode) => {
        setError('');
        setSuccessMessage('');
        setPassword('');
        setConfirmPassword('');
        setIsSignup(mode === 'signup');
        setIsForgotPassword(mode === 'forgot');
        if (mode !== 'reset') {
            setResetToken('');
            window.history.replaceState({}, '', window.location.pathname);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault(); // Зупиняємо стандартне перезавантаження сторінки браузером
        setError('');
        setSuccessMessage('');

        if ((isSignup || isResetPassword) && password !== confirmPassword) {
            setError('Паролі не збігаються.');
            return;
        }

        setLoading(true);

        try {
            if (isSignup) {
                await api.post('/auth/signup', { username, email, password });
                setIsSignup(false);
                setUsername('');
                setPassword('');
                setConfirmPassword('');
                setSuccessMessage('Реєстрацію завершено. Тепер увійдіть у свій акаунт.');
            } else if (isForgotPassword) {
                await api.post('/auth/request_password_reset', { email });
                setSuccessMessage('Якщо акаунт із цим email існує, посилання для відновлення вже надіслано.');
            } else if (isResetPassword) {
                await api.post(`/auth/reset_password/${resetToken}`, { password });
                switchMode('login');
                setSuccessMessage('Пароль оновлено. Тепер увійдіть із новим паролем.');
            } else {
                const formData = new URLSearchParams();
                formData.append('username', email);
                formData.append('password', password);
                const response = await api.post('/auth/login', formData, {
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
                });
                localStorage.setItem('token', response.data.access_token);
                onLoginSuccess();
            }
        } catch (err) {
            setError(getErrorMessage(err));
        } finally {
            setLoading(false);
        }
    };

    const title = isSignup
        ? 'Реєстрація у PhotoShare'
        : isForgotPassword
            ? 'Відновлення паролю'
            : isResetPassword
                ? 'Новий пароль'
                : 'Вхід у PhotoShare';

    return (
        <div style={{ maxWidth: '400px', margin: '50px auto', padding: '20px', border: '1px solid #ccc', borderRadius: '8px' }}>
            <h2>{title}</h2>

            {error && <p style={{ color: 'red' }}>{error}</p>}
            {successMessage && <p style={{ color: 'green' }}>{successMessage}</p>}

            <form onSubmit={handleSubmit}>
                {isSignup && <div style={{ marginBottom: '15px' }}>
                    <label style={{ display: 'block', marginBottom: '5px' }}>Username:</label>
                    <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} minLength={3} maxLength={50} required style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }} />
                </div>}

                {!isResetPassword && <div style={{ marginBottom: '15px' }}>
                    <label style={{ display: 'block', marginBottom: '5px' }}>Email:</label>
                    <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)} // Записуємо текст у стайт при введенні
                        required
                        style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
                    />
                </div>}

                {!isForgotPassword && <div style={{ marginBottom: '15px' }}>
                    <label style={{ display: 'block', marginBottom: '5px' }}>{isResetPassword ? 'Новий пароль:' : 'Пароль:'}</label>
                    <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        minLength={6}
                        required
                        style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
                    />
                </div>}

                {(isSignup || isResetPassword) && <div style={{ marginBottom: '15px' }}>
                    <label style={{ display: 'block', marginBottom: '5px' }}>Підтвердження пароля:</label>
                    <input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} minLength={6} required style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }} />
                </div>}

                <button type="submit" disabled={loading} style={{ width: '100%', padding: '10px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px', cursor: loading ? 'wait' : 'pointer' }}>
                    {loading ? 'Зачекайте...' : isSignup ? 'Зареєструватися' : isForgotPassword ? 'Надіслати посилання' : isResetPassword ? 'Зберегти пароль' : 'Увійти'}
                </button>
            </form>

            {!isResetPassword && <div style={{ marginTop: '16px', display: 'grid', gap: '8px', textAlign: 'center' }}>
                {!isForgotPassword && <button type="button" onClick={() => switchMode(isSignup ? 'login' : 'signup')} style={{ border: 'none', background: 'none', color: '#007bff', cursor: 'pointer' }}>
                    {isSignup ? 'Вже маєте акаунт? Увійти' : 'Немає акаунту? Зареєструватися'}
                </button>}
                {!isSignup && <button type="button" onClick={() => switchMode(isForgotPassword ? 'login' : 'forgot')} style={{ border: 'none', background: 'none', color: '#007bff', cursor: 'pointer' }}>
                    {isForgotPassword ? 'Повернутися до входу' : 'Забули пароль?'}
                </button>}
            </div>}
        </div>
    );
}

export default Login;
