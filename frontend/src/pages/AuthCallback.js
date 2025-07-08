import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';

const AuthCallback = () => {
  const [searchParams] = useSearchParams();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  const { login } = useAuth();

  useEffect(() => {
    const handleGoogleCallback = async () => {
      const code = searchParams.get('code');
      const error = searchParams.get('error');

      if (error) {
        setError('Authentication was cancelled or failed');
        setIsLoading(false);
        return;
      }

      if (!code) {
        setError('No authorization code received');
        setIsLoading(false);
        return;
      }

      try {
        // Send code to backend
        const response = await fetch('http://localhost:8000/api/v1/auth/google/callback', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ code }),
        });

        const data = await response.json();

        if (response.ok) {
          // Store token and user info
          localStorage.setItem('access_token', data.access_token);
          localStorage.setItem('user', JSON.stringify(data.user));
          
          // Update auth context
          login(data.user, data.access_token);
          
          toast.success('Successfully signed in with Google!');
          
          // Redirect based on user type
          if (data.user.is_admin) {
            navigate('/admin');
          } else {
            navigate('/dashboard');
          }
        } else {
          throw new Error(data.detail || 'Authentication failed');
        }
      } catch (error) {
        console.error('Google callback error:', error);
        setError(error.message || 'Authentication failed');
        toast.error('Authentication failed');
      } finally {
        setIsLoading(false);
      }
    };

    handleGoogleCallback();
  }, [searchParams, navigate, login]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
          <h2 className="text-lg font-medium text-gray-900 mb-2">
            Completing sign in...
          </h2>
          <p className="text-gray-600">
            Please wait while we verify your Google account.
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <h2 className="text-lg font-medium text-red-800 mb-2">
              Authentication Error
            </h2>
            <p className="text-red-600 text-sm">
              {error}
            </p>
          </div>
          
          <button
            onClick={() => navigate('/login')}
            className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 transition-colors"
          >
            Return to Login
          </button>
        </div>
      </div>
    );
  }

  return null;
};

export default AuthCallback;
