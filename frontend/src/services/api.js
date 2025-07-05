import axios from 'axios';
import toast from 'react-hot-toast';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

console.log('API_URL configured as:', API_URL);

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    } else if (error.response?.status >= 500) {
      toast.error('Erreur serveur. Veuillez réessayer plus tard.');
    } else if (!error.response) {
      toast.error('Problème de connexion au serveur.');
    }
    return Promise.reject(error);
  }
);

// Health check function
export const checkBackendHealth = async () => {
  try {
    const response = await api.get('/health/');
    console.log('Backend health check:', response.data);
    return response.data;
  } catch (error) {
    console.error('Health check failed:', error);
    return { status: 'error', error };
  }
};

// Auth endpoints
export const authAPI = {
  login: (email, password) => 
    api.post('/auth/login', new URLSearchParams({
      username: email,
      password: password,
    }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }),
  
  signup: async (userData) => {
    try {
      // Ensure we're sending exactly what the backend expects based on the UserCreate schema
      const data = {
        email: userData.email,
        password: userData.password,
        first_name: userData.firstName || null,
        last_name: userData.lastName || null
      };
      console.log('Signup request data:', data);
      // Use explicit content type header
      const response = await api.post('/users/signup', data, {
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
      });
      console.log('Signup response:', response);
      return response;
    } catch (error) {
      console.error('Signup error details:', {
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        message: error.message
      });
      throw error; // Re-throw to be handled by the caller
    }
  },
};

// User endpoints
export const userAPI = {
  me: () => api.get('/users/me'),
  updateMe: (data) => api.put('/users/me', data),
  updateOnboarding: (step, data) => 
    api.put('/users/me/onboarding', { step, data }),
  getAlertPreferences: () => api.get('/users/me/alert-preferences'),
  updateAlertPreferences: (data) => api.put('/users/me/alert-preferences', data),
};

// Flight endpoints
export const flightAPI = {
  getRoutes: (params) => api.get('/flights/routes', { params }),
  getDeals: (params) => api.get('/flights/deals', { params }),
};

// Alert endpoints
export const alertAPI = {
  getMyAlerts: (params) => api.get('/alerts/me', { params }),
};

export default api;