import apiClient from './apiClient.js';

export const INCIDENT_STATUSES = ['OPEN', 'INVESTIGATING', 'RESOLVED', 'CLOSED'];
export const INCIDENT_PRIORITIES = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];

export const incidentService = {
  async list({ page = 1, pageSize = 10 } = {}) {
    const response = await apiClient.get('/incidents', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  async create(payload) {
    const response = await apiClient.post('/incidents', payload);
    return response.data;
  },

  async update(id, payload) {
    const response = await apiClient.put(`/incidents/${id}`, payload);
    return response.data;
  },

  async remove(id) {
    await apiClient.delete(`/incidents/${id}`);
  },
};
