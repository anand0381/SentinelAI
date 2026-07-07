import apiClient from './apiClient.js';

export const authService = {
  async register(payload) {
    const response = await apiClient.post('/auth/register', payload);
    return response.data;
  },

  async login(payload) {
    const formData = new URLSearchParams({
      grant_type: 'password',
      username: payload.email.trim(),
      password: payload.password,
    });

    const response = await apiClient.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  },

  async me() {
    const response = await apiClient.get('/auth/me');
    return response.data;
  },

  async profile() {
    const response = await apiClient.get('/auth/profile');
    return response.data;
  },
};
