import React, { createContext, useState, useContext, useEffect } from 'react';
import { authAPI, userAPI } from '../services/api';
import toast from 'react-hot-toast';

const AuthContext = createContext({});

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check if user is logged in on mount
  useEffect(() => {
    console.log('AuthProvider: Checking authentication status...');
    checkAuth();
  }, []);

  const checkAuth = async () => {
    console.log('AuthProvider: Running checkAuth...');
    const token = localStorage.getItem('access_token');
    console.log('AuthProvider: Token exists?', !!token);
    
    if (token) {
      try {
        console.log('AuthProvider: Fetching user data...');
        const response = await userAPI.me();
        console.log('AuthProvider: User data received', response.data);
        setUser(response.data);
      } catch (error) {
        console.error('AuthProvider: Error fetching user data', error);
        localStorage.removeItem('access_token');
      }
    }
    console.log('AuthProvider: Setting loading to false');
    setLoading(false);
  };

  const login = async (email, password) => {
    try {
      console.log('AuthContext: Attempting login for email:', email);
      const response = await authAPI.login(email, password);
      const { access_token } = response.data;
      
      console.log('AuthContext: Login successful, token received');
      localStorage.setItem('access_token', access_token);
      
      // Get user data
      console.log('AuthContext: Fetching user profile data');
      const userResponse = await userAPI.me();
      setUser(userResponse.data);
      
      console.log('AuthContext: User data retrieved successfully', userResponse.data);
      toast.success('Connexion réussie !');
      return { success: true, user: userResponse.data };
    } catch (error) {
      console.error('AuthContext: Login error', error);
      
      let message = 'Erreur de connexion';
      
      if (error.response) {
        if (error.response.status === 400) {
          message = error.response.data?.detail || 'Email ou mot de passe incorrect';
        } else if (error.response.status === 401) {
          message = 'Authentification échouée';
        } else if (error.response.status >= 500) {
          message = 'Erreur serveur, veuillez réessayer plus tard';
        }
      } else if (error.request) {
        message = 'Impossible de contacter le serveur';
      }
      
      toast.error(message);
      return { success: false, error: message };
    }
  };

  const signup = async (userData) => {
    try {
      console.log('AuthContext: Attempting signup...');
      const response = await authAPI.signup(userData);
      const newUser = response.data;
      console.log('AuthContext: Signup successful, user created:', newUser);
      
      // Auto login after signup
      console.log('AuthContext: Attempting auto-login after signup...');
      const loginResult = await login(userData.email, userData.password);
      
      if (loginResult.success) {
        toast.success('Compte créé avec succès !');
        return { success: true, user: newUser };
      }
      
      return loginResult;
    } catch (error) {
      console.error('AuthContext: Signup error:', error);
      
      // More detailed error handling
      let message = 'Erreur lors de l\'inscription';
      let statusCode = error.response?.status;
      
      // Format error messages based on backend responses
      if (error.response) {
        if (statusCode === 400) {
          if (error.response.data?.detail === "A user with this email already exists") {
            message = "Un utilisateur avec cet email existe déjà";
          } else {
            message = error.response.data?.detail || 'Données invalides';
          }
        } else if (statusCode === 422) {
          message = 'Format de données incorrect';
          // For validation errors, get the first error message
          const firstError = Object.values(error.response.data?.detail || {})[0];
          if (Array.isArray(firstError) && firstError.length > 0) {
            message = firstError[0].msg || message;
          }
        } else if (statusCode === 0 || !statusCode) {
          message = 'Problème de connexion au serveur';
        }
      }
      
      toast.error(message);
      return { success: false, error: message, statusCode };
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    setUser(null);
    toast.success('Déconnexion réussie');
  };

  const updateUser = (updatedUser) => {
    setUser(updatedUser);
  };

  const value = {
    user,
    loading,
    login,
    signup,
    logout,
    updateUser,
    checkAuth,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};