import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { toast } from 'react-toastify';
import adminApi from '../services/adminApi';
import { Activity, AlertTriangle, Bot, CheckCircle, PlayCircle, PauseCircle, RefreshCw, Terminal } from 'lucide-react';

const AutonomousSystemTab = () => {
  const [autonomousData, setAutonomousData] = useState(null);
  const [performance, setPerformance] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [emergencyMode, setEmergencyMode] = useState(false);
  const [optimizing, setOptimizing] = useState(false);

  const fetchAutonomousData = async () => {
    try {
      const [statusData, performanceData, logsData] = await Promise.all([
        adminApi.getAutonomousStatus(),
        adminApi.getAutonomousPerformance(7),
        adminApi.getAutonomousLogs(50)
      ]);

      setAutonomousData(statusData);
      setPerformance(performanceData);
      setLogs(logsData.logs || []);
      setEmergencyMode(statusData.emergency_mode || false);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching autonomous data:', error);
      toast.error('Failed to load autonomous system data');
      setLoading(false);
    }
  };

  const handleEmergencyToggle = async () => {
    try {
      await adminApi.toggleEmergencyMode(!emergencyMode);
      setEmergencyMode(!emergencyMode);
      toast.success(emergencyMode ? 'Emergency mode disabled' : 'Emergency mode enabled');
      fetchAutonomousData();
    } catch (error) {
      console.error('Error toggling emergency mode:', error);
      toast.error('Failed to toggle emergency mode');
    }
  };

  const handleOptimizeRoutes = async () => {
    setOptimizing(true);
    try {
      await adminApi.optimizeRoutes();
      toast.success('Route optimization completed');
      fetchAutonomousData();
    } catch (error) {
      console.error('Error optimizing routes:', error);
      toast.error('Failed to optimize routes');
    } finally {
      setOptimizing(false);
    }
  };

  useEffect(() => {
    fetchAutonomousData();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchAutonomousData, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'bg-green-100 text-green-800';
      case 'warning': return 'bg-yellow-100 text-yellow-800';
      case 'critical': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy': return <CheckCircle className="w-4 h-4" />;
      case 'warning': return <AlertTriangle className="w-4 h-4" />;
      case 'critical': return <AlertTriangle className="w-4 h-4" />;
      default: return <Activity className="w-4 h-4" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Loading autonomous system data...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Status Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bot className="w-5 h-5" />
            Autonomous System Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600">System Status</span>
                <Badge className={getStatusColor(autonomousData?.status || 'unknown')}>
                  {getStatusIcon(autonomousData?.status || 'unknown')}
                  <span className="ml-1 capitalize">{autonomousData?.status || 'Unknown'}</span>
                </Badge>
              </div>
            </div>
            
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600">Emergency Mode</span>
                <Badge className={emergencyMode ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}>
                  {emergencyMode ? 'ACTIVE' : 'INACTIVE'}
                </Badge>
              </div>
            </div>
            
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600">Active Routes</span>
                <span className="text-lg font-semibold">{autonomousData?.active_routes || 0}</span>
              </div>
            </div>
            
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600">API Usage</span>
                <span className="text-lg font-semibold">{autonomousData?.quota_usage || 0}%</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Control Panel */}
      <Card>
        <CardHeader>
          <CardTitle>Control Panel</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <Button
              onClick={handleEmergencyToggle}
              variant={emergencyMode ? "destructive" : "default"}
              className="flex items-center gap-2"
            >
              {emergencyMode ? <PauseCircle className="w-4 h-4" /> : <PlayCircle className="w-4 h-4" />}
              {emergencyMode ? 'Disable Emergency Mode' : 'Enable Emergency Mode'}
            </Button>
            
            <Button
              onClick={handleOptimizeRoutes}
              disabled={optimizing}
              className="flex items-center gap-2"
            >
              <RefreshCw className={`w-4 h-4 ${optimizing ? 'animate-spin' : ''}`} />
              {optimizing ? 'Optimizing...' : 'Optimize Routes'}
            </Button>
            
            <Button
              onClick={fetchAutonomousData}
              variant="outline"
              className="flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh Data
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Performance Metrics */}
      {performance && (
        <Card>
          <CardHeader>
            <CardTitle>Performance Metrics (Last 7 Days)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-blue-50 rounded-lg">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-blue-700">Total Deals Found</span>
                  <span className="text-2xl font-bold text-blue-600">{performance.total_deals || 0}</span>
                </div>
              </div>
              
              <div className="p-4 bg-green-50 rounded-lg">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-green-700">API Calls Made</span>
                  <span className="text-2xl font-bold text-green-600">{performance.api_calls || 0}</span>
                </div>
              </div>
              
              <div className="p-4 bg-purple-50 rounded-lg">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-purple-700">Success Rate</span>
                  <span className="text-2xl font-bold text-purple-600">{performance.success_rate || 0}%</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Deals */}
      {performance?.recent_deals && performance.recent_deals.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Deal Discoveries</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {performance.recent_deals.slice(0, 5).map((deal, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <div className="font-medium">{deal.departure_city} → {deal.destination_city}</div>
                    <div className="text-sm text-gray-600">{deal.departure_date}</div>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold text-green-600">${deal.price}</div>
                    <div className="text-sm text-gray-500">{deal.deal_rating}/5</div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* System Logs */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Terminal className="w-5 h-5" />
            System Logs
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-gray-900 text-gray-100 p-4 rounded-lg font-mono text-sm max-h-64 overflow-y-auto">
            {logs.length > 0 ? (
              logs.map((log, index) => (
                <div key={index} className="mb-1">
                  <span className="text-gray-400">[{log.timestamp}]</span>
                  <span className={`ml-2 ${log.level === 'ERROR' ? 'text-red-400' : log.level === 'WARNING' ? 'text-yellow-400' : 'text-green-400'}`}>
                    {log.level}
                  </span>
                  <span className="ml-2">{log.message}</span>
                </div>
              ))
            ) : (
              <div className="text-gray-400">No logs available</div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AutonomousSystemTab;
