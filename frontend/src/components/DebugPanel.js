import React, { useState } from 'react';
import { testAPIEndpoint, testSignupFlow, testHealthCheck } from '../utils/debugTools';
import { checkBackendHealth } from '../services/api';

const DebugPanel = () => {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const runHealthCheck = async () => {
    setLoading(true);
    try {
      const result = await checkBackendHealth();
      setResults({
        test: 'API Health Check',
        data: result
      });
    } catch (error) {
      setResults({
        test: 'API Health Check',
        error: error.message
      });
    } finally {
      setLoading(false);
    }
  };

  const runDebugHealthCheck = async () => {
    setLoading(true);
    try {
      const result = await testHealthCheck();
      setResults({
        test: 'Debug Health Check',
        data: result
      });
    } catch (error) {
      setResults({
        test: 'Debug Health Check',
        error: error.message
      });
    } finally {
      setLoading(false);
    }
  };

  const runSignupTest = async () => {
    setLoading(true);
    try {
      const result = await testSignupFlow();
      setResults({
        test: 'Signup Flow Test',
        data: result
      });
    } catch (error) {
      setResults({
        test: 'Signup Flow Test',
        error: error.message
      });
    } finally {
      setLoading(false);
    }
  };

  const runOptionsTest = async () => {
    setLoading(true);
    try {
      const result = await testAPIEndpoint('/users/signup', 'OPTIONS');
      setResults({
        test: 'OPTIONS Request Test',
        data: result
      });
    } catch (error) {
      setResults({
        test: 'OPTIONS Request Test',
        error: error.message
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="border border-gray-200 rounded-lg p-4 my-4 bg-gray-50">
      <h2 className="text-lg font-bold mb-4">Debug Panel</h2>
      <div className="flex flex-wrap gap-2 mb-4">
        <button 
          onClick={runHealthCheck}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          Test API Health
        </button>
        <button 
          onClick={runDebugHealthCheck}
          disabled={loading}
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
        >
          Debug Health Check
        </button>
        <button 
          onClick={runOptionsTest}
          disabled={loading}
          className="px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700 disabled:opacity-50"
        >
          Test OPTIONS Request
        </button>
        <button 
          onClick={runSignupTest}
          disabled={loading}
          className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50"
        >
          Test Signup Flow
        </button>
      </div>

      {loading && (
        <div className="my-4 text-gray-600">Loading...</div>
      )}

      {results && (
        <div className="mt-4">
          <h3 className="font-semibold text-md mb-2">{results.test} Results:</h3>
          <pre className="bg-gray-800 text-gray-100 p-4 rounded overflow-auto max-h-80 text-sm">
            {JSON.stringify(results.data || results.error, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};

export default DebugPanel;
