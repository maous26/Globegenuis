import React from 'react';
import { FaGoogle } from 'react-icons/fa';

const GoogleAuthButton = ({ onSuccess, onError, className = '', children }) => {
  const handleGoogleAuth = async () => {
    try {
      // Get Google auth URL from backend
      const response = await fetch('/api/v1/auth/google/url');
      const data = await response.json();
      
      if (data.auth_url) {
        // Store callback handlers in sessionStorage for the callback page
        sessionStorage.setItem('google_auth_success', 'true');
        
        // Redirect to Google OAuth
        window.location.href = data.auth_url;
      } else {
        throw new Error('Failed to get Google auth URL');
      }
    } catch (error) {
      console.error('Google auth error:', error);
      if (onError) {
        onError(error);
      }
    }
  };

  return (
    <button
      onClick={handleGoogleAuth}
      className={`
        flex items-center justify-center w-full px-4 py-2 
        border border-gray-300 rounded-md shadow-sm 
        bg-white text-sm font-medium text-gray-700 
        hover:bg-gray-50 focus:outline-none focus:ring-2 
        focus:ring-offset-2 focus:ring-blue-500
        transition-colors duration-200
        ${className}
      `}
    >
      <FaGoogle className="w-5 h-5 mr-2 text-red-500" />
      {children || 'Continuer avec Google'}
    </button>
  );
};

export default GoogleAuthButton;
