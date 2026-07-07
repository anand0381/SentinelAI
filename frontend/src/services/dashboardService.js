import apiClient from './apiClient.js';

export const dashboardService = {
  async summary() {
    const response = await apiClient.get('/dashboard/summary');
    return response.data;
  },

  async threatSeverity() {
    const response = await apiClient.get('/dashboard/threat-severity');
    return response.data;
  },

  async threatCategory() {
    const response = await apiClient.get('/dashboard/threat-category');
    return response.data;
  },

  async incidentStatus() {
    const response = await apiClient.get('/dashboard/incident-status');
    return response.data;
  },

  async monthlyTrends() {
    const response = await apiClient.get('/dashboard/monthly-trends');
    return response.data;
  },

  async overview() {
    const [summary, threatSeverity, threatCategory, incidentStatus, monthlyTrends] =
      await Promise.all([
        this.summary(),
        this.threatSeverity(),
        this.threatCategory(),
        this.incidentStatus(),
        this.monthlyTrends(),
      ]);

    return {
      summary,
      threatSeverity,
      threatCategory,
      incidentStatus,
      monthlyTrends,
    };
  },
};
