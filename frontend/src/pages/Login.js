import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { motion } from 'framer-motion';
import { Plane, Mail, Lock } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import GoogleAuthButton from '../components/GoogleAuthButton';
import toast from 'react-hot-toast';

const Login = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [loading, setLoading] = useState(false);
  const [loginError, setLoginError] = useState('');
  
  const { register, handleSubmit, formState: { errors } } = useForm();

  const onSubmit = async (data) => {
    setLoading(true);
    setLoginError('');

    // Trim whitespace from inputs to avoid issues
    const trimmedEmail = data.email.trim();
    const trimmedPassword = data.password.trim();
    
    try {
      const result = await login(trimmedEmail, trimmedPassword);
      
      if (result.success) {
        // Redirect based on user type and onboarding status
        if (result.user.is_admin) {
          navigate('/admin');
        } else if (result.user.onboarding_completed) {
          navigate('/dashboard');
        } else {
          navigate('/onboarding');
        }
      } else {
        setLoginError(result.error || 'Échec de connexion');
      }
    } catch (error) {
      console.error('Login error:', error);
      setLoginError('Erreur de connexion au serveur');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleAuthError = (error) => {
    console.error('Google auth error:', error);
    toast.error('Erreur lors de l\'authentification Google');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 
                    flex items-center justify-center px-4">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md"
      >
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center space-x-2 mb-6">
            <Plane className="h-8 w-8 text-primary-600" />
            <span className="text-2xl font-bold">GlobeGenius</span>
          </Link>
          
          <h2 className="text-3xl font-bold text-gray-900">Bon retour !</h2>
          <p className="text-gray-600 mt-2">
            Connectez-vous pour accéder à vos alertes
          </p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Email
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
              <input
                type="email"
                {...register('email', { 
                  required: 'Email requis',
                  pattern: {
                    value: /^\S+@\S+$/i,
                    message: 'Email invalide'
                  }
                })}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg 
                         focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="vous@exemple.com"
              />
            </div>
            {errors.email && (
              <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Mot de passe
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
              <input
                type="password"
                {...register('password', { required: 'Mot de passe requis' })}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg 
                         focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="••••••••"
              />
            </div>
            {errors.password && (
              <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
            )}
          </div>

          <div className="flex items-center justify-between">
            <label className="flex items-center">
              <input type="checkbox" className="rounded text-primary-600" />
              <span className="ml-2 text-sm text-gray-600">Se souvenir de moi</span>
            </label>
            
            <Link to="/forgot-password" className="text-sm text-primary-600 hover:underline">
              Mot de passe oublié ?
            </Link>
          </div>

          {loginError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm mb-4">
              {loginError}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full btn-primary flex items-center justify-center"
          >
            {loading ? (
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" />
            ) : (
              'Se connecter'
            )}
          </button>

          {/* Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-gray-500">ou</span>
            </div>
          </div>

          {/* Google Auth Button */}
          <GoogleAuthButton 
            onError={handleGoogleAuthError}
            className="mb-6"
          />

        </form>

        <div className="mt-6 text-center">
          <p className="text-gray-600">
            Pas encore de compte ?{' '}
            <Link to="/signup" className="text-primary-600 font-semibold hover:underline">
              Inscrivez-vous
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
};

export default Login;