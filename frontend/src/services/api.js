// src/services/api.js
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle response errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth APIs
export const login = (credentials) => api.post('/auth/login', credentials);
export const logout = () => api.post('/auth/logout');
export const getCurrentUser = () => api.get('/auth/me');

// Card APIs
export const getCards = (params) => api.get('/cards', { params });
export const getCard = (id) => api.get(`/cards/${id}`);
export const createCard = (data) => api.post('/cards', data);
export const updateCard = (id, data) => api.put(`/cards/${id}`, data);
export const deleteCard = (id) => api.delete(`/cards/${id}`);

// Reader APIs
export const getReaders = () => api.get('/readers');
export const getReader = (id) => api.get(`/readers/${id}`);
export const createReader = (data) => api.post('/readers', data);
export const updateReader = (id, data) => api.put(`/readers/${id}`, data);

// Log APIs
export const getLogs = (params) => api.get('/logs', { params });
export const exportLogs = (params) => api.get('/logs/export/csv', { 
  params,
  responseType: 'blob' 
});

// Test endpoint untuk testing WebSocket
export const createTestLog = (params) => api.post('/logs/test/create', null, { params });

export default api;