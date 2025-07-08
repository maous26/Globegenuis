// services/adminApi.js
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class AdminApiService {
  constructor() {
    this.baseURL = `${API_BASE_URL}/api/v1/admin`;
  }

  async makeRequest(endpoint, options = {}) {
    const token = localStorage.getItem('access_token');
    
    const config = {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(`${this.baseURL}${endpoint}`, config);
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `HTTP ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error(`Admin API Error (${endpoint}):`, error);
      throw error;
    }
  }

  // Dashboard statistics
  async getDashboardStats() {
    return this.makeRequest('/dashboard/stats');
  }

  // Route performance
  async getRoutePerformance(days = 30) {
    return this.makeRequest(`/routes/performance?days=${days}`);
  }

  // Seasonal strategy visualization
  async getSeasonalVisualization() {
    return this.makeRequest('/seasonal/visualization');
  }

  // User analytics
  async getUserAnalytics(days = 30) {
    return this.makeRequest(`/users/analytics?days=${days}`);
  }

  // System health
  async getSystemHealth() {
    return this.makeRequest('/system/health');
  }

  // Scanner monitoring
  async getScannerMonitoring(hours = 24) {
    return this.makeRequest(`/monitoring/scanner?hours=${hours}`);
  }

  // Users list with pagination and search
  async getUsersList(params = {}) {
    const queryParams = new URLSearchParams(params).toString();
    return this.makeRequest(`/users/list?${queryParams}`);
  }

  // Trigger route scan
  async triggerRouteScan(routeId) {
    return this.makeRequest(`/routes/${routeId}/scan`, {
      method: 'POST',
    });
  }

  // Trigger tier scan
  async triggerTierScan(tier) {
    return this.makeRequest(`/routes/tier/${tier}/scan`, {
      method: 'POST',
    });
  }

  // Update route settings
  async updateRouteSettings(routeId, settings) {
    return this.makeRequest(`/routes/${routeId}/settings`, {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  }

  // Google OAuth URLs
  async getGoogleAuthUrl() {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/google/url`);
    return response.json();
  }

  // Google OAuth callback
  async handleGoogleCallback(code) {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/google/callback`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ code }),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Google authentication failed');
    }
    
    return response.json();
  }

  // Route expansion methods
  async getRouteExpansionStats() {
    return this.makeRequest('/routes/expansion/stats');
  }

  async getRouteSuggestions(count = 20, targetTier = 3) {
    return this.makeRequest(`/routes/expansion/suggestions?count=${count}&target_tier=${targetTier}`);
  }

  async addRoutesManually(routeConfigs) {
    return this.makeRequest('/routes/expansion/add-routes', {
      method: 'POST',
      body: JSON.stringify(routeConfigs),
    });
  }

  async smartNetworkExpansion(targetRoutes, focusArea = 'balanced') {
    return this.makeRequest('/routes/expansion/smart-expand', {
      method: 'POST',
      body: JSON.stringify({
        target_routes: targetRoutes,
        focus_area: focusArea
      }),
    });
  }

  async previewExpansion(targetRoutes, focusArea = 'balanced') {
    return this.makeRequest(`/routes/expansion/preview?target_routes=${targetRoutes}&focus_area=${focusArea}`);
  }

  // API KPIs
  async getApiKpis(timeframe = '24h') {
    return this.makeRequest(`/api/kpis?timeframe=${timeframe}`);
  }
}

export default new AdminApiService();
