import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { motion } from 'framer-motion';
import { Plane, Mail, Lock, Zap } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const Signup = () => {
  const navigate = useNavigate();
  const { signup } = useAuth();
  const [loading, setLoading] = useState(false);
  
  const { register, handleSubmit, watch, formState: { errors } } = useForm();
  const password = watch('password');

  const [signupError, setSignupError] = useState('');
  
  const onSubmit = async (data) => {
    setLoading(true);
    setSignupError('');
    
    // Create a new object with just the fields required by the backend
    // and exclude confirmPassword and terms which aren't needed in the API call
    const signupData = {
      email: data.email,
      password: data.password,
      // Optional fields using the proper field names for the backend
      firstName: data.firstName || null, // Will be mapped to first_name in the API service
      lastName: data.lastName || null    // Will be mapped to last_name in the API service
    };
    
    console.log('Submitting signup data:', signupData);
    
    try {
      const result = await signup(signupData);
      if (result.success) {
        console.log('Signup successful, navigating to onboarding', result.user);
        navigate('/onboarding');
      } else {
        console.error('Signup failed with error:', result.error);
        setSignupError(result.error || 'Une erreur est survenue lors de l\'inscription.');
      }
    } catch (error) {
      console.error('Signup submission error:', error);
      setSignupError('Problème de connexion au serveur. Veuillez réessayer.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 
                    flex items-center justify-center px-4 py-8">
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
          
          <h2 className="text-3xl font-bold text-gray-900">
            Créez votre compte
          </h2>
          <p className="text-gray-600 mt-2">
            Commencez à économiser sur vos voyages
          </p>
        </div>

        {/* Benefits */}
        <div className="bg-primary-50 rounded-lg p-4 mb-6">
          <div className="flex items-start space-x-3">
            <Zap className="h-5 w-5 text-primary-600 mt-0.5" />
            <div className="text-sm">
              <p className="font-semibold text-primary-900">
                Offre de lancement limitée
              </p>
              <p className="text-primary-700">
                7 jours gratuits puis 4,99€/mois seulement
              </p>
            </div>
          </div>
        </div>

        {signupError && (
          <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 rounded-md">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-700">{signupError}</p>
              </div>
            </div>
          </div>
        )}

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
                {...register('password', { 
                  required: 'Mot de passe requis',
                  minLength: {
                    value: 8,
                    message: 'Minimum 8 caractères'
                  }
                })}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg 
                         focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="••••••••"
              />
            </div>
            {errors.password && (
              <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Confirmer le mot de passe
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
              <input
                type="password"
                {...register('confirmPassword', { 
                  required: 'Confirmation requise',
                  validate: value => value === password || 'Les mots de passe ne correspondent pas'
                })}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg 
                         focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="••••••••"
              />
            </div>
            {errors.confirmPassword && (
              <p className="mt-1 text-sm text-red-600">{errors.confirmPassword.message}</p>
            )}
          </div>

          <div>
            <label className="flex items-start">
              <input 
                type="checkbox" 
                {...register('terms', { required: 'Vous devez accepter les conditions' })}
                className="rounded text-primary-600 mt-1" 
              />
              <span className="ml-2 text-sm text-gray-600">
                J'accepte les{' '}
                <Link to="/terms" className="text-primary-600 hover:underline">
                  conditions d'utilisation
                </Link>{' '}
                et la{' '}
                <Link to="/privacy" className="text-primary-600 hover:underline">
                  politique de confidentialité
                </Link>
              </span>
            </label>
            {errors.terms && (
              <p className="mt-1 text-sm text-red-600">{errors.terms.message}</p>
            )}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full btn-primary flex items-center justify-center"
          >
            {loading ? (
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" />
            ) : (
              'Créer mon compte'
            )}
          </button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-gray-600">
            Déjà un compte ?{' '}
            <Link to="/login" className="text-primary-600 font-semibold hover:underline">
              Connectez-vous
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
};

export default Signup;