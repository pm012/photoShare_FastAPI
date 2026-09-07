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

export default api;
