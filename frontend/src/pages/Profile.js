
import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { userAPI } from '../services/api';
import { motion } from 'framer-motion';
import { 
  User, 
  Mail, 
  Phone, 
  MapPin, 
  Bell, 
  Shield, 
  Edit2, 
  Save, 
  X, 
  ArrowLeft,
  LogOut,
  Plane,
  Heart,
  Calendar
} from 'lucide-react';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';

const Profile = () => {
  const { user, logout, updateUser } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    phone: '',
    email_notifications: true,
    sms_notifications: false,
    notification_frequency: 'instant'
  });

  useEffect(() => {
    if (user) {
      setFormData({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        phone: user.phone || '',
        email_notifications: user.email_notifications ?? true,
        sms_notifications: user.sms_notifications ?? false,
        notification_frequency: user.notification_frequency || 'instant'
      });
    }
  }, [user]);

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      const response = await userAPI.updateProfile(formData);
      updateUser(response.data);
      setIsEditing(false);
      toast.success('Profil mis à jour avec succès !');
    } catch (error) {
      toast.error('Erreur lors de la mise à jour du profil');
      console.error('Error updating profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    // Reset form data to original user data
    setFormData({
      first_name: user?.first_name || '',
      last_name: user?.last_name || '',
      phone: user?.phone || '',
      email_notifications: user?.email_notifications ?? true,
      sms_notifications: user?.sms_notifications ?? false,
      notification_frequency: user?.notification_frequency || 'instant'
    });
    setIsEditing(false);
  };

  const formatTier = (tier) => {
    const tierMap = {
      'free': 'Gratuit',
      'essential': 'Essentiel',
      'premium': 'Premium',
      'premium_plus': 'Premium Plus'
    };
    return tierMap[tier] || tier;
  };

  const getTierColor = (tier) => {
    const colorMap = {
      'free': 'bg-gray-100 text-gray-800',
      'essential': 'bg-blue-100 text-blue-800',
      'premium': 'bg-purple-100 text-purple-800',
      'premium_plus': 'bg-gold-100 text-gold-800'
    };
    return colorMap[tier] || 'bg-gray-100 text-gray-800';
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Accès refusé</h2>
          <p className="text-gray-600 mb-4">Vous devez être connecté pour accéder à cette page.</p>
          <Link to="/login" className="text-indigo-600 hover:text-indigo-500">
            Se connecter
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link 
                to="/dashboard" 
                className="flex items-center text-gray-600 hover:text-gray-900 transition"
              >
                <ArrowLeft className="h-5 w-5 mr-2" />
                Retour au tableau de bord
              </Link>
            </div>
            <div className="flex items-center space-x-4">
              {!isEditing ? (
                <button
                  onClick={() => setIsEditing(true)}
                  className="flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
                >
                  <Edit2 className="h-5 w-5 mr-2" />
                  Modifier
                </button>
              ) : (
                <div className="flex items-center space-x-2">
                  <button
                    onClick={handleCancel}
                    className="flex items-center px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition"
                  >
                    <X className="h-5 w-5 mr-2" />
                    Annuler
                  </button>
                  <button
                    onClick={handleSave}
                    disabled={loading}
                    className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition disabled:opacity-50"
                  >
                    <Save className="h-5 w-5 mr-2" />
                    {loading ? 'Enregistrement...' : 'Enregistrer'}
                  </button>
                </div>
              )}
              <button
                onClick={logout}
                className="flex items-center px-3 py-2 text-red-600 bg-red-50 rounded-lg hover:bg-red-100 transition"
              >
                <LogOut className="h-5 w-5 mr-2" />
                Déconnexion
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Profile Header */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-lg shadow-sm p-6 mb-6"
          >
            <div className="flex items-center space-x-4 mb-6">
              <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center">
                <User className="h-8 w-8 text-indigo-600" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  {user.first_name || user.last_name 
                    ? `${user.first_name || ''} ${user.last_name || ''}`.trim()
                    : user.email?.split('@')[0] || 'Utilisateur'
                  }
                </h1>
                <p className="text-gray-600">{user.email}</p>
                <div className="flex items-center space-x-2 mt-2">
                  <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getTierColor(user.tier)}`}>
                    {formatTier(user.tier)}
                  </span>
                  <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                    user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {user.is_active ? 'Actif' : 'Inactif'}
                  </span>
                </div>
              </div>
            </div>
          </motion.div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Personal Information */}
            <motion.div 
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-white rounded-lg shadow-sm p-6"
            >
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <User className="h-5 w-5 mr-2" />
                Informations personnelles
              </h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Prénom
                  </label>
                  {isEditing ? (
                    <input
                      type="text"
                      name="first_name"
                      value={formData.first_name}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      placeholder="Votre prénom"
                    />
                  ) : (
                    <p className="text-gray-900">{user.first_name || 'Non défini'}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nom
                  </label>
                  {isEditing ? (
                    <input
                      type="text"
                      name="last_name"
                      value={formData.last_name}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      placeholder="Votre nom"
                    />
                  ) : (
                    <p className="text-gray-900">{user.last_name || 'Non défini'}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email
                  </label>
                  <div className="flex items-center">
                    <Mail className="h-4 w-4 text-gray-400 mr-2" />
                    <p className="text-gray-900">{user.email}</p>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Téléphone
                  </label>
                  {isEditing ? (
                    <input
                      type="tel"
                      name="phone"
                      value={formData.phone}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      placeholder="Votre numéro de téléphone"
                    />
                  ) : (
                    <div className="flex items-center">
                      <Phone className="h-4 w-4 text-gray-400 mr-2" />
                      <p className="text-gray-900">{user.phone || 'Non défini'}</p>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>

            {/* Notification Preferences */}
            <motion.div 
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-white rounded-lg shadow-sm p-6"
            >
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <Bell className="h-5 w-5 mr-2" />
                Préférences de notification
              </h2>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-gray-700">
                    Notifications par email
                  </label>
                  {isEditing ? (
                    <input
                      type="checkbox"
                      name="email_notifications"
                      checked={formData.email_notifications}
                      onChange={handleInputChange}
                      className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                    />
                  ) : (
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                      user.email_notifications ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {user.email_notifications ? 'Activé' : 'Désactivé'}
                    </span>
                  )}
                </div>

                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-gray-700">
                    Notifications par SMS
                  </label>
                  {isEditing ? (
                    <input
                      type="checkbox"
                      name="sms_notifications"
                      checked={formData.sms_notifications}
                      onChange={handleInputChange}
                      className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                    />
                  ) : (
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                      user.sms_notifications ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {user.sms_notifications ? 'Activé' : 'Désactivé'}
                    </span>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Fréquence des notifications
                  </label>
                  {isEditing ? (
                    <select
                      name="notification_frequency"
                      value={formData.notification_frequency}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      <option value="instant">Instantané</option>
                      <option value="daily">Quotidien</option>
                      <option value="weekly">Hebdomadaire</option>
                    </select>
                  ) : (
                    <p className="text-gray-900">
                      {user.notification_frequency === 'instant' ? 'Instantané' :
                       user.notification_frequency === 'daily' ? 'Quotidien' :
                       user.notification_frequency === 'weekly' ? 'Hebdomadaire' : 
                       user.notification_frequency}
                    </p>
                  )}
                </div>
              </div>
            </motion.div>

            {/* Travel Preferences */}
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="bg-white rounded-lg shadow-sm p-6"
            >
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <Plane className="h-5 w-5 mr-2" />
                Préférences de voyage
              </h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Aéroports de départ
                  </label>
                  <div className="flex items-center">
                    <MapPin className="h-4 w-4 text-gray-400 mr-2" />
                    <p className="text-gray-900">
                      {user.home_airports?.length > 0 
                        ? user.home_airports.join(', ') 
                        : 'Aucun aéroport défini'}
                    </p>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Destinations favorites
                  </label>
                  <div className="flex items-center">
                    <Heart className="h-4 w-4 text-gray-400 mr-2" />
                    <p className="text-gray-900">
                      {user.favorite_destinations?.length > 0 
                        ? user.favorite_destinations.join(', ') 
                        : 'Aucune destination favorite'}
                    </p>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Types de voyage
                  </label>
                  <div className="flex items-center">
                    <Calendar className="h-4 w-4 text-gray-400 mr-2" />
                    <p className="text-gray-900">
                      {user.travel_types?.length > 0 
                        ? user.travel_types.join(', ') 
                        : 'Aucun type de voyage défini'}
                    </p>
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Account Status */}
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="bg-white rounded-lg shadow-sm p-6"
            >
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <Shield className="h-5 w-5 mr-2" />
                Statut du compte
              </h2>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">Compte vérifié</span>
                  <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                    user.is_verified ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {user.is_verified ? 'Vérifié' : 'Non vérifié'}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">Statut du compte</span>
                  <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                    user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {user.is_active ? 'Actif' : 'Inactif'}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">Abonnement</span>
                  <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getTierColor(user.tier)}`}>
                    {formatTier(user.tier)}
                  </span>
                </div>

                {user.subscription_expires_at && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">Expire le</span>
                    <span className="text-sm text-gray-900">
                      {new Date(user.subscription_expires_at).toLocaleDateString('fr-FR')}
                    </span>
                  </div>
                )}
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;