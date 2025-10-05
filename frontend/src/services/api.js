import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth
export const login = (credentials) => 
  api.post('/auth/login', credentials);

// Cards
export const getCards = (params) => 
  api.get('/cards', { params });

export const createCard = (data) => 
  api.post('/cards', data);

export const updateCard = (id, data) => 
  api.put(`/cards/${id}`, data);

export const deleteCard = (id) => 
  api.delete(`/cards/${id}`);

// Readers
export const getReaders = () => 
  api.get('/readers');

export const createReader = (data) => 
  api.post('/readers', data);

// Logs
export const getLogs = (params) => 
  api.get('/logs', { params });

export const exportLogs = (params) => 
  api.get('/logs/export/csv', { 
    params, 
    responseType: 'blob' 
  });

export default api;