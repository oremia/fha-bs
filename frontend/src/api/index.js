import axios from 'axios';

// 使用相对路径，以便devServer代理
const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json'
  }
});

export default {
  getConfig() {
    return apiClient.get('/config');
  },
  getFhaData() {
    return apiClient.get('/fha-data');
  },
  createNewProject(skeleton) {
    return apiClient.post('/new-project', { skeleton });
  },
  importFromExcel(file) {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post('/import-excel', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  exportToExcel() {
    return apiClient.get('/export-excel', { responseType: 'blob' });
  },
  addRow() {
    return apiClient.post('/add-row');
  },
  deleteRows(indices) {
    return apiClient.post('/delete-rows', { indices });
  },
  updateEntry(index, data) {
    return apiClient.put(`/update-entry`, {index, data});
  },
  runWizard(source_index, results) {
    return apiClient.post('/run-wizard', { source_index, results });
  },
  getDashboardData() {
    return apiClient.get('/dashboard-data');
  }
};