import React, { useState } from 'react';
import api from './api';

function Login({ onLoginSuccess }) {
    // Створюємо пам'ять (стан) для полів вводу
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');

    // Функція, яка спрацює при натисканні на кнопку "Увійти"
    const handleSubmit = async (e) => {
        e.preventDefault(); // Зупиняємо стандартне перезавантаження сторінки браузером
        setError('');

        // Бекенд очікує Form Data, тому пакуємо дані через URLSearchParams
        const formData = new URLSearchParams();
        formData.append('username', email); // Наш FastAPI очікує email в полі 'username'
        formData.append('password', password);

        try {
            // Робимо запит до нашого FastAPI
            const response = await api.post('/auth/login', formData, {
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
            });

            // Якщо все успішно, дістаємо токен
            const token = response.data.access_token;

            // Зберігаємо токен у пам'ять браузера, щоб він не зникав при оновленні сторінки
            localStorage.setItem('token', token);

            // Викликаємо функцію успіху, яку передамо з головного компонента App
            onLoginSuccess();
        } catch (err) {
            // Обробляємо помилки (наприклад, неправильний пароль або ліміт запитів 429)
            setError(err.response?.data?.detail || 'Щось пішло не так. Спробуйте пізніше.');
        }
    };

    return (
        <div style={{ maxWidth: '400px', margin: '50px auto', padding: '20px', border: '1px solid #ccc', borderRadius: '8px' }}>
            <h2>Вхід у PhotoShare</h2>

            {error && <p style={{ color: 'red' }}>{error}</p>}

            <form onSubmit={handleSubmit}>
                <div style={{ marginBottom: '15px' }}>
                    <label style={{ display: 'block', marginBottom: '5px' }}>Email:</label>
                    <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)} // Записуємо текст у стайт при введенні
                        required
                        style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
                    />
                </div>

                <div style={{ marginBottom: '15px' }}>
                    <label style={{ display: 'block', marginBottom: '5px' }}>Пароль:</label>
                    <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                        style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
                    />
                </div>

                <button type="submit" style={{ width: '100%', padding: '10px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                    Увійти
                </button>
            </form>
        </div>
    );
}

export default Login;
