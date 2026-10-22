import { useState } from 'react';
import api from './api';
import './Login.css';

const COPY = {
    login: { title: 'Sign in', subtitle: 'Welcome back to PhotoShare.', submit: 'Sign in' },
    signup: { title: 'Create an account', subtitle: 'Join PhotoShare to share your photos.', submit: 'Create account' },
    forgot: { title: 'Reset your password', subtitle: "Enter your email and we'll send you a recovery link.", submit: 'Send recovery link' },
    reset: { title: 'Set a new password', subtitle: 'Choose a new password for your account.', submit: 'Save password' },
};

const getErrorMessage = (err) => {
    const detail = err.response?.data?.detail;
    if (Array.isArray(detail)) {
        return detail.map((item) => item.msg).join(' ');
    }
    return detail || 'Something went wrong. Please try again later.';
};

// Password input with a Show/Hide toggle. Defined outside Login so it keeps its state while typing.
function PasswordField({ id, label, value, onChange, autoComplete, hint, hintIsError = false, labelAside }) {
    const [visible, setVisible] = useState(false);

    return (
        <div className="lg-field">
            <div className="lg-label-row">
                <label className="lg-label" htmlFor={id}>{label}</label>
                {labelAside}
            </div>
            <div className="lg-password">
                <input id={id} className="field" type={visible ? 'text' : 'password'} value={value} onChange={onChange} minLength={6} autoComplete={autoComplete} required />
                <button className="lg-toggle" type="button" onClick={() => setVisible((current) => !current)} aria-pressed={visible} aria-label={visible ? 'Hide password' : 'Show password'}>
                    {visible ? 'Hide' : 'Show'}
                </button>
            </div>
            {hint && <small className={hintIsError ? 'lg-hint is-error' : 'lg-hint'} aria-live="polite">{hint}</small>}
        </div>
    );
}

function Login({ onLoginSuccess }) {
    // Track the values entered in the form.
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [username, setUsername] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [resetToken, setResetToken] = useState(() => new URLSearchParams(window.location.search).get('reset_token') || '');
    const [mode, setMode] = useState(() => (new URLSearchParams(window.location.search).get('reset_token') ? 'reset' : 'login')); // login | signup | forgot | reset
    const [loading, setLoading] = useState(false);
    const [successMessage, setSuccessMessage] = useState('');
    const [error, setError] = useState('');

    const copy = COPY[mode];
    const needsConfirmation = mode === 'signup' || mode === 'reset';
    const passwordsMismatch = needsConfirmation && confirmPassword !== '' && password !== confirmPassword;

    const switchMode = (nextMode) => {
        setError('');
        setSuccessMessage('');
        setPassword('');
        setConfirmPassword('');
        setMode(nextMode);
        if (nextMode !== 'reset') {
            setResetToken('');
            window.history.replaceState({}, '', window.location.pathname);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault(); // Prevent the browser's default form submission.
        setError('');
        setSuccessMessage('');

        if (needsConfirmation && password !== confirmPassword) {
            setError('Passwords do not match.');
            return;
        }

        setLoading(true);

        try {
            if (mode === 'signup') {
                await api.post('/auth/signup', { username, email, password });
                setMode('login');
                setUsername('');
                setPassword('');
                setConfirmPassword('');
                setSuccessMessage('Registration complete. You can now sign in.');
            } else if (mode === 'forgot') {
                await api.post('/auth/request_password_reset', { email });
                setSuccessMessage('If an account with this email exists, a recovery link has been sent.');
            } else if (mode === 'reset') {
                await api.post(`/auth/reset_password/${resetToken}`, { password });
                switchMode('login');
                setSuccessMessage('Password updated. Sign in with your new password.');
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

    return (
        <main className="lg-page">
            <div className="lg-card">
                <p className="lg-brand">PhotoShare</p>
                <h1 className="lg-title">{copy.title}</h1>
                <p className="lg-subtitle">{copy.subtitle}</p>

                {error && <p className="error-message" role="alert">{error}</p>}
                {successMessage && <p className="success-message" role="status">{successMessage}</p>}

                <form className="lg-form" onSubmit={handleSubmit}>
                    {mode === 'signup' && (
                        <div className="lg-field">
                            <label className="lg-label" htmlFor="auth-username">Username</label>
                            <input id="auth-username" className="field" type="text" value={username} onChange={(e) => setUsername(e.target.value)} minLength={3} maxLength={50} autoComplete="username" required autoFocus />
                        </div>
                    )}

                    {mode !== 'reset' && (
                        <div className="lg-field">
                            <label className="lg-label" htmlFor="auth-email">Email</label>
                            <input id="auth-email" className="field" type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" required autoFocus={mode !== 'signup'} />
                        </div>
                    )}

                    {mode !== 'forgot' && (
                        <PasswordField
                            id="auth-password"
                            label={mode === 'reset' ? 'New password' : 'Password'}
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                            hint={mode === 'login' ? '' : 'At least 6 characters'}
                            labelAside={mode === 'login' && <button className="lg-link" type="button" onClick={() => switchMode('forgot')}>Forgot password?</button>}
                        />
                    )}

                    {needsConfirmation && (
                        <PasswordField
                            id="auth-confirm-password"
                            label="Confirm password"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            autoComplete="new-password"
                            hint={passwordsMismatch ? 'Passwords do not match' : ''}
                            hintIsError
                        />
                    )}

                    <button className="btn btn-primary" type="submit" disabled={loading}>
                        {loading ? 'Please wait...' : copy.submit}
                    </button>
                </form>

                <div className="lg-footer">
                    {mode === 'login' && <p>New to PhotoShare? <button className="lg-link" type="button" onClick={() => switchMode('signup')}>Create an account</button></p>}
                    {mode === 'signup' && <p>Already have an account? <button className="lg-link" type="button" onClick={() => switchMode('login')}>Sign in</button></p>}
                    {(mode === 'forgot' || mode === 'reset') && <p><button className="lg-link" type="button" onClick={() => switchMode('login')}>Back to sign in</button></p>}
                </div>
            </div>
        </main>
    );
}

export default Login;