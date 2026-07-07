import apiClient from './apiClient.js';

export const THREAT_CATEGORIES = [
  'Malware',
  'Phishing',
  'Ransomware',
  'DDoS',
  'Insider Threat',
  'Vulnerability',
  'Other',
];

export const THREAT_SEVERITIES = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];
export const THREAT_STATUSES = ['NEW', 'INVESTIGATING', 'MITIGATED', 'CLOSED'];

function buildParams(params) {
  return Object.fromEntries(
    Object.entries(params).filter(
      ([, value]) => value !== '' && value !== null && value !== undefined,
    ),
  );
}

export const threatService = {
  async list({ page = 1, pageSize = 10 } = {}) {
    const response = await apiClient.get('/threats', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  async search({ query, page = 1, pageSize = 10 } = {}) {
    const response = await apiClient.get('/threats/search', {
      params: { q: query, page, page_size: pageSize },
    });
    return response.data;
  },

  async filter({
    category,
    severity,
    status,
    source,
    page = 1,
    pageSize = 10,
  } = {}) {
    const response = await apiClient.get('/threats/filter', {
      params: buildParams({
        category,
        severity,
        status,
        source,
        page,
        page_size: pageSize,
      }),
    });
    return response.data;
  },

  async get(id) {
    const response = await apiClient.get(`/threats/${id}`);
    return response.data;
  },

  async create(payload) {
    const response = await apiClient.post('/threats', payload);
    return response.data;
  },

  async update(id, payload) {
    const response = await apiClient.put(`/threats/${id}`, payload);
    return response.data;
  },

  async remove(id) {
    await apiClient.delete(`/threats/${id}`);
  },
};
