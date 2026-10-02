import { useState } from 'react';
import api from './api';

function Login({ onLoginSuccess }) {
    // Track the values entered in the form.
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
        return detail || 'Something went wrong. Please try again later.';
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
        e.preventDefault(); // Prevent the browser's default form submission.
        setError('');
        setSuccessMessage('');

        if ((isSignup || isResetPassword) && password !== confirmPassword) {
            setError('Passwords do not match.');
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
                setSuccessMessage('Registration complete. You can now sign in.');
            } else if (isForgotPassword) {
                await api.post('/auth/request_password_reset', { email });
                setSuccessMessage('If an account with this email exists, a recovery link has been sent.');
            } else if (isResetPassword) {
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

    const title = isSignup
        ? 'Create a PhotoShare account'
        : isForgotPassword
            ? 'Password recovery'
            : isResetPassword
                ? 'Set a new password'
                : 'Sign in to PhotoShare';

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
                        onChange={(e) => setEmail(e.target.value)} // Update the state as the user types.
                        required
                        style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
                    />
                </div>}

                {!isForgotPassword && <div style={{ marginBottom: '15px' }}>
                    <label style={{ display: 'block', marginBottom: '5px' }}>{isResetPassword ? 'New password:' : 'Password:'}</label>
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
                    <label style={{ display: 'block', marginBottom: '5px' }}>Confirm password:</label>
                    <input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} minLength={6} required style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }} />
                </div>}

                <button type="submit" disabled={loading} style={{ width: '100%', padding: '10px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px', cursor: loading ? 'wait' : 'pointer' }}>
                    {loading ? 'Please wait...' : isSignup ? 'Create account' : isForgotPassword ? 'Send recovery link' : isResetPassword ? 'Save password' : 'Sign in'}
                </button>
            </form>

            {!isResetPassword && <div style={{ marginTop: '16px', display: 'grid', gap: '8px', textAlign: 'center' }}>
                {!isForgotPassword && <button type="button" onClick={() => switchMode(isSignup ? 'login' : 'signup')} style={{ border: 'none', background: 'none', color: '#007bff', cursor: 'pointer' }}>
                    {isSignup ? 'Already have an account? Sign in' : 'New to PhotoShare? Create an account'}
                </button>}
                {!isSignup && <button type="button" onClick={() => switchMode(isForgotPassword ? 'login' : 'forgot')} style={{ border: 'none', background: 'none', color: '#007bff', cursor: 'pointer' }}>
                    {isForgotPassword ? 'Back to sign in' : 'Forgot password?'}
                </button>}
            </div>}
        </div>
    );
}

export default Login;
