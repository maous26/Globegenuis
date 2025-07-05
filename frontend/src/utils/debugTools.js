import axios from 'axios';

/**
 * Debug function to test API connectivity with various HTTP methods
 * @param {string} endpoint - The API endpoint to test, e.g., '/users/signup'
 * @param {string} method - HTTP method to use ('GET', 'POST', 'OPTIONS')
 * @param {Object} data - The payload to send for POST requests
 * @returns {Promise} - The axios response
 */
export const testAPIEndpoint = async (endpoint, method = 'OPTIONS', data = null) => {
  try {
    const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';
    const fullUrl = `${API_URL}${endpoint}`;
    
    console.log(`Testing ${method} request to ${fullUrl}`);
    
    const config = {
      method,
      url: fullUrl,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    };
    
    if (data && (method === 'POST' || method === 'PUT')) {
      config.data = data;
    }
    
    const response = await axios(config);
    console.log(`Test ${method} succeeded:`, {
      status: response.status,
      statusText: response.statusText,
      headers: response.headers,
      data: response.data
    });
    
    return { success: true, response };
  } catch (error) {
    console.error(`Test ${method} failed:`, {
      status: error.response?.status,
      statusText: error.response?.statusText,
      headers: error.response?.headers,
      data: error.response?.data,
      message: error.message
    });
    
    return { 
      success: false, 
      error,
      status: error.response?.status,
      data: error.response?.data
    };
  }
};

/**
 * Test signup flow with a test user
 * @returns {Promise} - The test results
 */
export const testSignupFlow = async () => {
  // 1. First try an OPTIONS request to check CORS
  const optionsResult = await testAPIEndpoint('/users/signup', 'OPTIONS');
  
  if (!optionsResult.success) {
    return { 
      success: false, 
      message: 'OPTIONS request failed - CORS issue detected',
      details: optionsResult
    };
  }
  
  // 2. Try a POST with a test user
  const testUser = {
    email: `test-${Date.now()}@example.com`,
    password: 'password123',
    first_name: 'Test',
    last_name: 'User'
  };
  
  const postResult = await testAPIEndpoint('/users/signup', 'POST', testUser);
  
  return {
    success: postResult.success,
    message: postResult.success 
      ? 'Signup test successful' 
      : 'Signup test failed',
    details: {
      options: optionsResult,
      signup: postResult
    }
  };
};

/**
 * Test API health check
 * @returns {Promise} - The test result
 */
export const testHealthCheck = async () => {
  return await testAPIEndpoint('/health/', 'GET');
};
