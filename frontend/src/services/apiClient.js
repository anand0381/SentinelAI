import axios from 'axios';

import { clearStoredSession, getStoredToken } from '../utils/storage.js';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

let unauthorizedHandler = null;

export function setUnauthorizedHandler(handler) {
  unauthorizedHandler = handler;
}

apiClient.interceptors.request.use((config) => {
  const token = getStoredToken();
  const requestUrl = config.url || '';
  const isPublicAuthRequest =
    requestUrl.endsWith('/auth/login') || requestUrl.endsWith('/auth/register');

  if (token && !isPublicAuthRequest) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearStoredSession();

      if (unauthorizedHandler) {
        unauthorizedHandler();
      }
    }

    return Promise.reject(error);
  },
);

export default apiClient;
