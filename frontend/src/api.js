import axios from 'axios';

// Створюємо ізольований екземпляр axios з базовою адресою нашого FastAPI
const api = axios.create({
  baseURL: 'http://localhost:8000/api',
});

// Інтерцептор (перехоплювач): перед КОЖНИМ запитом до бекенду
// він перевіряє, чи є в браузері збережений токен, і якщо є — додає його в заголовки
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

api.interceptors.response.use((response) => response, (error) => {
  const status = error.response?.status;
  const requestUrl = error.config?.url || '';
  const isLoginRequest = requestUrl.includes('/auth/login');
  const detail = String(error.response?.data?.detail || '').toLowerCase();
  const isInactiveAccount = status === 403 && (detail.includes('banned') || detail.includes('inactive'));

  if ((status === 401 || isInactiveAccount) && !isLoginRequest) {
    localStorage.removeItem('token');
    window.dispatchEvent(new Event('photoshare-auth-expired'));
  }

  return Promise.reject(error);
});

export default api;
