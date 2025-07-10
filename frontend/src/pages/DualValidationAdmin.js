import React, { useState, useEffect } from 'react';
import { CheckCircle, XCircle, AlertTriangle, Activity, Settings, TestTube, RefreshCw, Shield } from 'lucide-react';
import toast from 'react-hot-toast';
import adminApi from '../services/adminApi';

const DualValidationAdmin = () => {
  const [status, setStatus] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [testResult, setTestResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [testLoading, setTestLoading] = useState(false);

  // Form states for testing
  const [testOrigin, setTestOrigin] = useState('CDG');
  const [testDestination, setTestDestination] = useState('MAD');
  const [testPrice, setTestPrice] = useState(150);

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const data = await adminApi.getDualValidationStatus();
      setStatus(data);
    } catch (error) {
      console.error('Error fetching status:', error);
      toast.error('Failed to fetch dual validation status');
    } finally {
      setLoading(false);
    }
  };

  const fetchMetrics = async () => {
    try {
      const data = await adminApi.getDualValidationMetrics(7);
      setMetrics(data);
    } catch (error) {
      console.error('Error fetching metrics:', error);
    }
  };

  const testRouteValidation = async () => {
    setTestLoading(true);
    try {
      const data = await adminApi.testRouteValidation(testOrigin, testDestination, testPrice);
      setTestResult(data);
      toast.success('Route validation test completed');
    } catch (error) {
      console.error('Error testing route validation:', error);
      toast.error('Failed to test route validation');
    } finally {
      setTestLoading(false);
    }
  };

  const testTravelPayouts = async () => {
    setLoading(true);
    try {
      const data = await adminApi.testTravelPayoutsConnection();
      toast.success(`TravelPayouts Test: ${data.connection_status || 'Completed'}`);
    } catch (error) {
      console.error('Error testing TravelPayouts:', error);
      toast.error('Failed to test TravelPayouts connection');
    } finally {
      setLoading(false);
    }
  };

  const reValidateDeals = async () => {
    setLoading(true);
    try {
      const data = await adminApi.reValidateDeals();
      toast.success(`Re-validated ${data.results?.deals_processed || 0} deals`);
      fetchMetrics(); // Refresh metrics
    } catch (error) {
      console.error('Error re-validating deals:', error);
      toast.error('Failed to re-validate deals');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    fetchMetrics();
  }, []);

  const getStatusIcon = (systemStatus) => {
    switch (systemStatus) {
      case 'operational':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'degraded':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      default:
        return <XCircle className="h-5 w-5 text-red-500" />;
    }
  };

  const getStatusColor = (systemStatus) => {
    switch (systemStatus) {
      case 'operational':
        return 'bg-green-100 text-green-800';
      case 'degraded':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-red-100 text-red-800';
    }
  };

  const Badge = ({ children, className }) => (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${className}`}>
      {children}
    </span>
  );

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold flex items-center">
          <Shield className="h-8 w-8 mr-3 text-blue-600" />
          Dual API Validation System
        </h1>
        <button 
          onClick={() => { fetchStatus(); fetchMetrics(); }} 
          disabled={loading}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* System Status */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium flex items-center">
            <Settings className="h-5 w-5 mr-2" />
            System Status
          </h3>
        </div>
        <div className="p-6">
          {status ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  {getStatusIcon(status.system_status)}
                  <span className="font-medium">Overall Status</span>
                </div>
                <Badge className={getStatusColor(status.system_status)}>
                  {status.system_status}
                </Badge>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center justify-between">
                  <span>TravelPayouts API</span>
                  <Badge className={status.travelpayouts_configured ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                    {status.travelpayouts_configured ? 'Configured' : 'Missing'}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span>AviationStack API</span>
                  <Badge className={status.aviationstack_configured ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                    {status.aviationstack_configured ? 'Configured' : 'Missing'}
                  </Badge>
                </div>
              </div>

              {status.statistics && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">{status.statistics.total_deals}</div>
                    <div className="text-sm text-gray-500">Total Deals</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">{status.statistics.active_deals}</div>
                    <div className="text-sm text-gray-500">Active Deals</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600">{status.statistics.high_confidence_deals}</div>
                    <div className="text-sm text-gray-500">High Confidence</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-orange-600">{status.statistics.validation_rate?.toFixed(1)}%</div>
                    <div className="text-sm text-gray-500">Validation Rate</div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-4">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-gray-500">Loading system status...</p>
            </div>
          )}
        </div>
      </div>

      {/* Testing Tools */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium flex items-center">
            <TestTube className="h-5 w-5 mr-2" />
            Testing Tools
          </h3>
        </div>
        <div className="p-6 space-y-6">
          {/* Route Validation Test */}
          <div className="space-y-4">
            <h4 className="font-medium">Test Route Validation</h4>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Origin</label>
                <input
                  type="text"
                  value={testOrigin}
                  onChange={(e) => setTestOrigin(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="CDG"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Destination</label>
                <input
                  type="text"
                  value={testDestination}
                  onChange={(e) => setTestDestination(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="MAD"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Test Price (€)</label>
                <input
                  type="number"
                  value={testPrice}
                  onChange={(e) => setTestPrice(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="150"
                />
              </div>
            </div>
            <div className="flex space-x-4">
              <button
                onClick={testRouteValidation}
                disabled={testLoading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {testLoading ? 'Testing...' : 'Test Validation'}
              </button>
              <button
                onClick={testTravelPayouts}
                disabled={loading}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
              >
                Test TravelPayouts
              </button>
              <button
                onClick={reValidateDeals}
                disabled={loading}
                className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50"
              >
                Re-validate Deals
              </button>
            </div>
          </div>

          {/* Test Results */}
          {testResult && (
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <h5 className="font-medium mb-2">Test Results</h5>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Route:</span>
                  <span className="font-mono">{testResult.test_parameters.route}</span>
                </div>
                <div className="flex justify-between">
                  <span>Test Price:</span>
                  <span className="font-mono">€{testResult.test_parameters.test_price}</span>
                </div>
                <div className="flex justify-between">
                  <span>Validation Result:</span>
                  <Badge className={testResult.validation_result.is_valid ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                    {testResult.validation_result.is_valid ? 'Valid' : 'Invalid'}
                  </Badge>
                </div>
                <div className="flex justify-between">
                  <span>Confidence Score:</span>
                  <span className="font-mono">{testResult.validation_result.confidence_score}</span>
                </div>
                <div className="flex justify-between">
                  <span>Recommendation:</span>
                  <Badge className={testResult.recommendation === 'approve' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                    {testResult.recommendation}
                  </Badge>
                </div>
                {testResult.validation_result.reasons && (
                  <div className="mt-2">
                    <span className="font-medium">Reasons:</span>
                    <ul className="list-disc list-inside ml-4">
                      {testResult.validation_result.reasons.map((reason, index) => (
                        <li key={index} className="text-gray-600">{reason}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Emergency Mode */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium flex items-center">
            <AlertTriangle className="h-5 w-5 mr-2 text-yellow-500" />
            Emergency Controls
          </h3>
        </div>
        <div className="p-6">
          <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
            <div className="flex">
              <AlertTriangle className="h-5 w-5 text-yellow-400" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-yellow-800">
                  Emergency Validation Mode
                </h3>
                <div className="mt-2 text-sm text-yellow-700">
                  <p>
                    In emergency mode, the system will use TravelPayouts API only for validation
                    when AviationStack is unavailable. Use this mode sparingly to preserve API quotas.
                  </p>
                </div>
                <div className="mt-4">
                  <button
                    onClick={() => {
                      toast.info('Emergency mode controls available in production environment');
                    }}
                    className="text-sm bg-yellow-100 text-yellow-800 hover:bg-yellow-200 px-3 py-2 rounded-md border border-yellow-300"
                  >
                    Configure Emergency Mode
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DualValidationAdmin;
