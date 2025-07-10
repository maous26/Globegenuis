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

  // Round-trip metrics
  async getRoundTripMetrics(days = 30) {
    return this.makeRequest(`/round-trip/metrics?days=${days}`);
  }

  // Admin Settings
  async getAdminSettings() {
    return this.makeRequest('/settings');
  }

  async updateAdminSettings(settings) {
    return this.makeRequest('/settings', {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  }

  // Test Email Methods
  async sendTestEmail() {
    return this.makeRequest('/test-email', {
      method: 'POST',
    });
  }

  async sendTestAlert() {
    return this.makeRequest('/test-alert', {
      method: 'POST',
    });
  }

  // Dual Validation Methods
  async getDualValidationStatus() {
    return this.makeRequest('/dual-validation/dual-validation/status');
  }

  async getDualValidationMetrics(days = 7) {
    return this.makeRequest(`/dual-validation/dual-validation/metrics?days=${days}`);
  }

  async testTravelPayoutsConnection() {
    return this.makeRequest('/dual-validation/dual-validation/travelpayouts-test', {
      method: 'GET',
    });
  }

  async testRouteValidation(origin, destination, price) {
    return this.makeRequest(`/dual-validation/dual-validation/test-route?origin=${origin}&destination=${destination}&test_price=${price}`, {
      method: 'POST',
    });
  }

  async reValidateDeals() {
    return this.makeRequest('/dual-validation/dual-validation/re-validate-deals', {
      method: 'POST',
    });
  }

  async setEmergencyMode(active) {
    return this.makeRequest('/dual-validation/dual-validation/emergency-mode', {
      method: 'POST',
      body: JSON.stringify({
        active: active
      }),
    });
  }

  // Autonomous System Methods
  async getAutonomousStatus() {
    return this.makeRequest('/autonomous/status');
  }

  async toggleEmergencyMode(active) {
    return this.makeRequest('/autonomous/emergency', {
      method: 'POST',
      body: JSON.stringify(active),
    });
  }

  async optimizeRoutes() {
    return this.makeRequest('/autonomous/optimize', {
      method: 'POST',
    });
  }

  async getAutonomousPerformance(days = 7) {
    return this.makeRequest(`/autonomous/performance?days=${days}`);
  }

  async getAutonomousLogs(lines = 100) {
    return this.makeRequest(`/autonomous/logs?lines=${lines}`);
  }
}

export default new AdminApiService();
