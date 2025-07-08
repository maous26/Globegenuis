import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import AdminApiService from '../services/adminApi';
import { 
  Users, 
  Plane, 
  DollarSign, 
  Bell, 
  Activity, 
  TrendingUp,
  Settings,
  Eye,
  BarChart3,
  MapPin,
  Clock,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Zap,
  Plus,
  Network,
  Globe
} from 'lucide-react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import toast from 'react-hot-toast';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

const AdminDashboard = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const adminApi = AdminApiService;
  const [dashboardData, setDashboardData] = useState(null);
  const [routePerformance, setRoutePerformance] = useState([]);
  const [seasonalData, setSeasonalData] = useState(null);
  const [userAnalytics, setUserAnalytics] = useState(null);
  const [systemHealth, setSystemHealth] = useState(null);
  const [monitoringData, setMonitoringData] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  
  // Route expansion state
  const [expansionStats, setExpansionStats] = useState(null);
  const [routeSuggestions, setRouteSuggestions] = useState([]);
  const [expansionPreview, setExpansionPreview] = useState(null);
  const [expansionLoading, setExpansionLoading] = useState(false);

  useEffect(() => {
    console.log('AdminDashboard: User object:', user);
    console.log('AdminDashboard: Is admin?', user?.is_admin);
    
    if (!user?.is_admin) {
      console.log('AdminDashboard: Access denied - user is not admin');
      toast.error('Access denied: Admin privileges required');
      return;
    }
    
    console.log('AdminDashboard: Loading dashboard data...');
    loadDashboardData();
  }, [user]);

  useEffect(() => {
    if (activeTab === 'expansion' && !expansionStats) {
      loadExpansionData();
    }
  }, [activeTab]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load all dashboard data in parallel using AdminApiService
      const [
        stats,
        routes,
        seasonal,
        analytics,
        health,
        monitoring
      ] = await Promise.all([
        adminApi.getDashboardStats(),
        adminApi.getRoutePerformance(30),
        adminApi.getSeasonalVisualization(),
        adminApi.getUserAnalytics(30),
        adminApi.getSystemHealth(),
        adminApi.getScannerMonitoring(24)
      ]);

      setDashboardData(stats);
      setRoutePerformance(routes);
      setSeasonalData(seasonal);
      setUserAnalytics(analytics);
      setSystemHealth(health);
      setMonitoringData(monitoring);

    } catch (error) {
      console.error('Error loading dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const loadExpansionData = async () => {
    try {
      setExpansionLoading(true);
      const [stats, suggestions] = await Promise.all([
        adminApi.getRouteExpansionStats(),
        adminApi.getRouteSuggestions(20, 3)
      ]);
      
      setExpansionStats(stats);
      setRouteSuggestions(suggestions);
    } catch (error) {
      console.error('Error loading expansion data:', error);
      toast.error('Failed to load expansion data');
    } finally {
      setExpansionLoading(false);
    }
  };

  const triggerRouteScan = async (routeId) => {
    try {
      const result = await adminApi.triggerRouteScan(routeId);
      toast.success(`Scan started for route ${result.route}`);
    } catch (error) {
      console.error('Error triggering route scan:', error);
      toast.error('Failed to trigger route scan');
    }
  };

  const triggerTierScan = async (tier) => {
    try {
      const result = await adminApi.triggerTierScan(tier);
      toast.success(`Scan started for ${result.routes_count} Tier ${tier} routes`);
    } catch (error) {
      console.error('Error triggering tier scan:', error);
      toast.error('Failed to trigger tier scan');
    }
  };

  const handleSmartExpansion = async (targetRoutes, focusArea) => {
    try {
      setExpansionLoading(true);
      const result = await adminApi.smartNetworkExpansion(targetRoutes, focusArea);
      
      toast.success(`Successfully added ${result.total_added} new routes!`);
      
      // Reload expansion data
      await loadExpansionData();
      
      // Reload dashboard stats
      await loadDashboardData();
      
    } catch (error) {
      console.error('Error during smart expansion:', error);
      toast.error('Failed to expand network');
    } finally {
      setExpansionLoading(false);
    }
  };

  const handlePreviewExpansion = async (targetRoutes, focusArea) => {
    try {
      setExpansionLoading(true);
      const preview = await adminApi.previewExpansion(targetRoutes, focusArea);
      setExpansionPreview(preview);
    } catch (error) {
      console.error('Error previewing expansion:', error);
      toast.error('Failed to preview expansion');
    } finally {
      setExpansionLoading(false);
    }
  };

  if (!user?.is_admin) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <XCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h1>
          <p className="text-gray-600">Admin privileges required to access this page.</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold text-gray-700">Loading Admin Dashboard...</h2>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
              <p className="text-gray-600">Monitor and manage GlobeGenius operations</p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                {systemHealth?.status === 'healthy' ? (
                  <CheckCircle className="h-5 w-5 text-green-500" />
                ) : (
                  <AlertTriangle className="h-5 w-5 text-yellow-500" />
                )}
                <span className={`text-sm font-medium ${
                  systemHealth?.status === 'healthy' ? 'text-green-700' : 'text-yellow-700'
                }`}>
                  System {systemHealth?.status || 'Unknown'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {[
              { id: 'overview', name: 'Overview', icon: BarChart3 },
              { id: 'routes', name: 'Route Monitoring', icon: MapPin },
              { id: 'expansion', name: 'Route Expansion', icon: Network },
              { id: 'seasonal', name: 'Seasonal Strategy', icon: Activity },
              { id: 'users', name: 'User Analytics', icon: Users },
              { id: 'system', name: 'System Health', icon: Settings }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2`}
              >
                <tab.icon className="h-4 w-4" />
                <span>{tab.name}</span>
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Tab Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'overview' && (
          <OverviewTab 
            data={dashboardData} 
            monitoring={monitoringData}
            onTriggerTierScan={triggerTierScan}
          />
        )}
        {activeTab === 'routes' && (
          <RouteMonitoringTab 
            routes={routePerformance}
            onTriggerScan={triggerRouteScan}
          />
        )}
        {activeTab === 'expansion' && (
          <RouteExpansionTab 
            stats={expansionStats}
            suggestions={routeSuggestions}
            preview={expansionPreview}
            loading={expansionLoading}
            adminApi={adminApi}
            onLoadData={loadExpansionData}
            onSmartExpansion={handleSmartExpansion}
            onPreviewExpansion={handlePreviewExpansion}
          />
        )}
        {activeTab === 'seasonal' && (
          <SeasonalStrategyTab data={seasonalData} />
        )}
        {activeTab === 'users' && (
          <UserAnalyticsTab data={userAnalytics} />
        )}
        {activeTab === 'system' && (
          <SystemHealthTab 
            health={systemHealth} 
            monitoring={monitoringData}
          />
        )}
      </div>
    </div>
  );
};

// Overview Tab Component
const OverviewTab = ({ data, monitoring, onTriggerTierScan }) => {
  if (!data) return <div>Loading...</div>;

  const StatCard = ({ title, value, change, icon: Icon, color = 'blue' }) => (
    <div className="bg-white overflow-hidden shadow rounded-lg">
      <div className="p-5">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <Icon className={`h-6 w-6 text-${color}-600`} />
          </div>
          <div className="ml-5 w-0 flex-1">
            <dl>
              <dt className="text-sm font-medium text-gray-500 truncate">{title}</dt>
              <dd className="text-lg font-medium text-gray-900">{value}</dd>
              {change && (
                <dd className="text-sm text-gray-600">{change}</dd>
              )}
            </dl>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Users"
          value={data.users?.total?.toLocaleString() || '0'}
          change={`+${data.users?.new_week || 0} this week`}
          icon={Users}
          color="blue"
        />
        <StatCard
          title="Active Routes"
          value={data.routes?.active || '0'}
          change={`${data.routes?.total || 0} total routes`}
          icon={MapPin}
          color="green"
        />
        <StatCard
          title="Active Deals"
          value={data.deals?.active || '0'}
          change={`+${data.deals?.today || 0} today`}
          icon={DollarSign}
          color="yellow"
        />
        <StatCard
          title="API Calls Today"
          value={monitoring?.api_quota?.used_today?.toLocaleString() || '0'}
          change={`${monitoring?.api_quota?.remaining || 0} remaining`}
          icon={Activity}
          color={monitoring?.api_quota?.usage_percentage > 90 ? 'red' : 'blue'}
        />
      </div>

      {/* API Quota Progress */}
      {monitoring?.api_quota && (
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Daily API Quota Usage</h3>
          <div className="space-y-4">
            <div className="flex justify-between text-sm text-gray-600">
              <span>Used: {monitoring.api_quota.used_today}</span>
              <span>Limit: {monitoring.api_quota.daily_limit}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className={`h-2 rounded-full ${
                  monitoring.api_quota.usage_percentage > 90 ? 'bg-red-600' :
                  monitoring.api_quota.usage_percentage > 70 ? 'bg-yellow-600' : 'bg-green-600'
                }`}
                style={{ width: `${Math.min(monitoring.api_quota.usage_percentage, 100)}%` }}
              />
            </div>
            <div className="text-sm text-gray-600">
              {monitoring.api_quota.usage_percentage.toFixed(1)}% used
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => onTriggerTierScan(1)}
            className="flex items-center justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700"
          >
            <Zap className="h-4 w-4 mr-2" />
            Scan Tier 1 Routes
          </button>
          <button
            onClick={() => onTriggerTierScan(2)}
            className="flex items-center justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-yellow-600 hover:bg-yellow-700"
          >
            <Zap className="h-4 w-4 mr-2" />
            Scan Tier 2 Routes
          </button>
          <button
            onClick={() => onTriggerTierScan(3)}
            className="flex items-center justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
          >
            <Zap className="h-4 w-4 mr-2" />
            Scan Tier 3 Routes
          </button>
        </div>
      </div>
    </div>
  );
};

// Route Monitoring Tab Component
const RouteMonitoringTab = ({ routes, onTriggerScan }) => {
  const [sortBy, setSortBy] = useState('deals_found');
  const [filterTier, setFilterTier] = useState('all');

  const filteredRoutes = routes
    .filter(route => filterTier === 'all' || route.tier === parseInt(filterTier))
    .sort((a, b) => {
      switch (sortBy) {
        case 'deals_found':
          return b.deals_found - a.deals_found;
        case 'efficiency':
          return b.efficiency - a.efficiency;
        case 'avg_discount':
          return b.avg_discount - a.avg_discount;
        default:
          return 0;
      }
    });

  return (
    <div className="space-y-6">
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-gray-900">Route Performance</h3>
          <div className="flex space-x-4">
            <select
              value={filterTier}
              onChange={(e) => setFilterTier(e.target.value)}
              className="rounded-md border-gray-300 text-sm"
            >
              <option value="all">All Tiers</option>
              <option value="1">Tier 1</option>
              <option value="2">Tier 2</option>
              <option value="3">Tier 3</option>
            </select>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="rounded-md border-gray-300 text-sm"
            >
              <option value="deals_found">Deals Found</option>
              <option value="efficiency">Efficiency</option>
              <option value="avg_discount">Avg Discount</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Route
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tier
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Deals Found
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Avg Discount
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Efficiency
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredRoutes.slice(0, 20).map((route) => (
                <tr key={route.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {route.route}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      route.tier === 1 ? 'bg-green-100 text-green-800' :
                      route.tier === 2 ? 'bg-yellow-100 text-yellow-800' :
                      'bg-blue-100 text-blue-800'
                    }`}>
                      Tier {route.tier}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {route.deals_found}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {route.avg_discount.toFixed(1)}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {(route.efficiency * 100).toFixed(1)}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <button
                      onClick={() => onTriggerScan(route.id)}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      Scan Now
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// Seasonal Strategy Tab Component
const SeasonalStrategyTab = ({ data }) => {
  if (!data) return <div>Loading seasonal data...</div>;

  return (
    <div className="space-y-6">
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Seasonal Strategy for {data.current_month}
        </h3>
        
        {data.active_seasonal_routes && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.active_seasonal_routes.map((route, index) => (
              <div key={index} className="border rounded-lg p-4">
                <h4 className="font-medium text-gray-900">{route.route}</h4>
                <p className="text-sm text-gray-600 capitalize">Period: {route.period}</p>
                <p className="text-sm text-gray-600">Tier: {route.tier}</p>
                <p className="text-sm text-gray-600">Frequency: {route.scan_frequency}</p>
              </div>
            ))}
          </div>
        )}

        {data.optimization_recommendations && data.optimization_recommendations.length > 0 && (
          <div className="mt-6">
            <h4 className="font-medium text-gray-900 mb-2">Optimization Recommendations</h4>
            <ul className="list-disc list-inside space-y-1">
              {data.optimization_recommendations.map((rec, index) => (
                <li key={index} className="text-sm text-gray-600">{rec}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

// User Analytics Tab Component
const UserAnalyticsTab = ({ data }) => {
  if (!data) return <div>Loading user analytics...</div>;

  // Prepare chart data
  const registrationChartData = {
    labels: data.daily_registrations?.map(d => new Date(d.date).toLocaleDateString()) || [],
    datasets: [
      {
        label: 'New Registrations',
        data: data.daily_registrations?.map(d => d.count) || [],
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.1,
      },
    ],
  };

  const tierChartData = {
    labels: data.engagement_by_tier?.map(t => t.tier) || [],
    datasets: [
      {
        label: 'Alerts per User',
        data: data.engagement_by_tier?.map(t => t.alerts_per_user) || [],
        backgroundColor: [
          'rgba(34, 197, 94, 0.8)',
          'rgba(59, 130, 246, 0.8)',
          'rgba(168, 85, 247, 0.8)',
          'rgba(245, 158, 11, 0.8)',
        ],
      },
    ],
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Daily Registrations</h3>
          <Line data={registrationChartData} />
        </div>
        
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Engagement by Tier</h3>
          <Doughnut data={tierChartData} />
        </div>
      </div>
    </div>
  );
};

// System Health Tab Component
const SystemHealthTab = ({ health, monitoring }) => {
  if (!health || !monitoring) return <div>Loading system health...</div>;

  const scanChartData = {
    labels: monitoring.hourly_scans?.map(s => new Date(s.hour).toLocaleTimeString()) || [],
    datasets: [
      {
        label: 'Scans per Hour',
        data: monitoring.hourly_scans?.map(s => s.scan_count) || [],
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        tension: 0.1,
      },
      {
        label: 'Deals per Hour',
        data: monitoring.hourly_deals?.map(d => d.deal_count) || [],
        borderColor: 'rgb(245, 158, 11)',
        backgroundColor: 'rgba(245, 158, 11, 0.1)',
        tension: 0.1,
      },
    ],
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white shadow rounded-lg p-6">
          <h4 className="text-sm font-medium text-gray-500">System Status</h4>
          <div className="mt-2 flex items-center">
            {health.status === 'healthy' ? (
              <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
            ) : (
              <AlertTriangle className="h-5 w-5 text-yellow-500 mr-2" />
            )}
            <span className="text-lg font-semibold capitalize">{health.status}</span>
          </div>
        </div>
        
        <div className="bg-white shadow rounded-lg p-6">
          <h4 className="text-sm font-medium text-gray-500">Recent Scans</h4>
          <p className="text-2xl font-semibold mt-2">{health.recent_scans}</p>
        </div>
        
        <div className="bg-white shadow rounded-lg p-6">
          <h4 className="text-sm font-medium text-gray-500">Recent Deals</h4>
          <p className="text-2xl font-semibold mt-2">{health.recent_deals}</p>
        </div>
      </div>

      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Scanner Activity (24h)</h3>
        <Line data={scanChartData} />
      </div>
    </div>
  );
};

// Route Expansion Tab Component
const RouteExpansionTab = ({ 
  stats, 
  suggestions, 
  preview, 
  loading, 
  adminApi,
  onLoadData, 
  onSmartExpansion, 
  onPreviewExpansion 
}) => {
  const [targetRoutes, setTargetRoutes] = useState(100);
  const [focusArea, setFocusArea] = useState('balanced');
  const [showPreview, setShowPreview] = useState(false);
  const [selectedSuggestions, setSelectedSuggestions] = useState([]);

  const handlePreview = async () => {
    await onPreviewExpansion(targetRoutes, focusArea);
    setShowPreview(true);
  };

  const handleExecuteExpansion = async () => {
    await onSmartExpansion(targetRoutes, focusArea);
    setShowPreview(false);
  };

  const handleAddSelectedRoutes = async () => {
    if (selectedSuggestions.length === 0) {
      toast.error('Please select at least one route to add');
      return;
    }

    try {
      const result = await adminApi.addRoutesManually(selectedSuggestions.map(index => {
        const suggestion = suggestions[index];
        return {
          origin: suggestion.origin,
          destination: suggestion.destination,
          tier: suggestion.suggested_tier
        };
      }));

      toast.success(`Successfully added ${result.total_added} routes!`);
      setSelectedSuggestions([]);
      await onLoadData();
    } catch (error) {
      console.error('Error adding routes:', error);
      toast.error('Failed to add routes');
    }
  };

  const toggleSuggestionSelection = (index) => {
    setSelectedSuggestions(prev => 
      prev.includes(index) 
        ? prev.filter(i => i !== index)
        : [...prev, index]
    );
  };

  if (loading && !stats) {
    return (
      <div className="flex justify-center items-center py-20">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Current Network Stats */}
      {stats && (
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Current Network Overview</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600">{stats.total_routes}</div>
              <div className="text-sm text-gray-500">Total Routes</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600">{stats.tier_distribution?.tier_1 || 0}</div>
              <div className="text-sm text-gray-500">Tier 1 Routes</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-yellow-600">{stats.tier_distribution?.tier_2 || 0}</div>
              <div className="text-sm text-gray-500">Tier 2 Routes</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-600">{stats.tier_distribution?.tier_3 || 0}</div>
              <div className="text-sm text-gray-500">Tier 3 Routes</div>
            </div>
          </div>
          
          {stats.coverage_gaps && stats.coverage_gaps.length > 0 && (
            <div className="mt-4 p-4 bg-yellow-50 rounded-lg">
              <h4 className="font-medium text-yellow-800 mb-2">Coverage Gaps Identified</h4>
              <ul className="text-sm text-yellow-700 space-y-1">
                {stats.coverage_gaps.map((gap, index) => (
                  <li key={index}>• {gap}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Smart Expansion Tool */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Smart Network Expansion</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Target Total Routes
            </label>
            <input
              type="number"
              value={targetRoutes}
              onChange={(e) => setTargetRoutes(parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              min={stats?.total_routes || 0}
              max="500"
            />
            <p className="text-sm text-gray-500 mt-1">
              Current: {stats?.total_routes || 0} routes
            </p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Focus Strategy
            </label>
            <select
              value={focusArea}
              onChange={(e) => setFocusArea(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="balanced">Balanced Growth</option>
              <option value="domestic">Domestic Focus</option>
              <option value="international">International Focus</option>
              <option value="vacation">Vacation Destinations</option>
            </select>
          </div>
        </div>

        <div className="mt-6 flex space-x-4">
          <button
            onClick={handlePreview}
            disabled={loading}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            <Eye className="h-5 w-5 mr-2" />
            Preview Expansion
          </button>
          
          <button
            onClick={handleExecuteExpansion}
            disabled={loading}
            className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
          >
            <Zap className="h-5 w-5 mr-2" />
            Execute Expansion
          </button>
        </div>
      </div>

      {/* Expansion Preview */}
      {showPreview && preview && (
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Expansion Preview</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{preview.routes_to_add}</div>
              <div className="text-sm text-gray-600">Routes to Add</div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{preview.current_total}</div>
              <div className="text-sm text-gray-600">Current Total</div>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">{preview.expansion_strategy}</div>
              <div className="text-sm text-gray-600">Focus Strategy</div>
            </div>
          </div>

          {preview.preview_routes && (
            <div>
              <h4 className="font-medium text-gray-900 mb-3">Sample Routes to Add</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {preview.preview_routes.map((route, index) => (
                  <div key={index} className="p-3 bg-gray-50 rounded-lg">
                    <div className="font-medium">{route.origin} → {route.destination}</div>
                    <div className="text-sm text-gray-600">
                      Tier {route.suggested_tier} • Priority: {route.priority_score}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {route.route_type}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="mt-6 flex space-x-4">
            <button
              onClick={handleExecuteExpansion}
              disabled={loading}
              className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
            >
              <CheckCircle className="h-5 w-5 mr-2" />
              Confirm & Execute
            </button>
            <button
              onClick={() => setShowPreview(false)}
              className="flex items-center px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
            >
              <XCircle className="h-5 w-5 mr-2" />
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Route Suggestions */}
      {suggestions && suggestions.length > 0 && (
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Intelligent Route Suggestions</h3>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-500">
                {selectedSuggestions.length} selected
              </span>
              {selectedSuggestions.length > 0 && (
                <button
                  onClick={handleAddSelectedRoutes}
                  disabled={loading}
                  className="flex items-center px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:opacity-50"
                >
                  <Plus className="h-4 w-4 mr-1" />
                  Add Selected
                </button>
              )}
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    <input
                      type="checkbox"
                      checked={selectedSuggestions.length === suggestions.length}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedSuggestions(suggestions.map((_, index) => index));
                        } else {
                          setSelectedSuggestions([]);
                        }
                      }}
                      className="rounded text-blue-600"
                    />
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Route
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Tier
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Priority Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Reason
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {suggestions.map((suggestion, index) => (
                  <tr key={index}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <input
                        type="checkbox"
                        checked={selectedSuggestions.includes(index)}
                        onChange={() => toggleSuggestionSelection(index)}
                        className="rounded text-blue-600"
                      />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {suggestion.origin} → {suggestion.destination}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        suggestion.suggested_tier === 1 ? 'bg-green-100 text-green-800' :
                        suggestion.suggested_tier === 2 ? 'bg-yellow-100 text-yellow-800' :
                        'bg-blue-100 text-blue-800'
                      }`}>
                        Tier {suggestion.suggested_tier}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {suggestion.priority_score}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {suggestion.route_type || 'General'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;
