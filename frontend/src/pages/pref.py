import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Plane, MapPin, Heart, Bell, Check, ChevronRight, 
  ChevronLeft, Home, Briefcase, Users, Palmtree,
  Settings, Euro, Calendar, Globe, X, Save
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { userAPI } from '../services/api';
import toast from 'react-hot-toast';

const DESTINATIONS = [
  { code: 'NYC', name: 'New York', region: 'Amérique du Nord', emoji: '🗽' },
  { code: 'LAX', name: 'Los Angeles', region: 'Amérique du Nord', emoji: '🌴' },
  { code: 'MIA', name: 'Miami', region: 'Amérique du Nord', emoji: '🏖️' },
  { code: 'CUN', name: 'Cancún', region: 'Amérique Centrale', emoji: '🏝️' },
  { code: 'GRU', name: 'São Paulo', region: 'Amérique du Sud', emoji: '🌆' },
  { code: 'DXB', name: 'Dubaï', region: 'Moyen-Orient', emoji: '🏙️' },
  { code: 'BKK', name: 'Bangkok', region: 'Asie', emoji: '🏛️' },
  { code: 'NRT', name: 'Tokyo', region: 'Asie', emoji: '🗾' },
  { code: 'SIN', name: 'Singapour', region: 'Asie', emoji: '🌃' },
  { code: 'SYD', name: 'Sydney', region: 'Océanie', emoji: '🌊' },
  { code: 'JNB', name: 'Johannesburg', region: 'Afrique', emoji: '🦁' },
  { code: 'MAR', name: 'Marrakech', region: 'Afrique', emoji: '🕌' },
];

const TRAVEL_TYPES = [
  { 
    id: 'leisure', 
    name: 'Loisirs', 
    icon: Palmtree, 
    description: 'Vacances et escapades',
    color: 'bg-green-100 text-green-700'
  },
  { 
    id: 'business', 
    name: 'Affaires', 
    icon: Briefcase, 
    description: 'Voyages professionnels',
    color: 'bg-blue-100 text-blue-700'
  },
  { 
    id: 'family', 
    name: 'Famille', 
    icon: Users, 
    description: 'Voyages en famille',
    color: 'bg-purple-100 text-purple-700'
  },
  { 
    id: 'adventure', 
    name: 'Aventure', 
    icon: MapPin, 
    description: 'Exploration et découverte',
    color: 'bg-orange-100 text-orange-700'
  },
];

const Preferences = () => {
  const navigate = useNavigate();
  const { user, updateUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('destinations');
  
  const [preferences, setPreferences] = useState({
    favoriteDestinations: [],
    travelTypes: [],
    alertSettings: {
      minDiscount: 30,
      maxPriceEurope: 200,
      maxPriceInternational: 800,
      instantAlerts: true,
      weeklyDigest: false
    },
    travelDates: {
      flexible: true,
      excludeMonths: []
    }
  });

  useEffect(() => {
    // Load existing preferences
    if (user) {
      setPreferences(prev => ({
        ...prev,
        favoriteDestinations: user.favorite_destinations || [],
        travelTypes: user.travel_types || []
      }));
      
      // Load alert preferences
      loadAlertPreferences();
    }
  }, [user]);

  const loadAlertPreferences = async () => {
    try {
      const response = await userAPI.getAlertPreferences();
      setPreferences(prev => ({
        ...prev,
        alertSettings: {
          minDiscount: response.data.min_discount_percentage || 30,
          maxPriceEurope: response.data.max_price_europe || 200,
          maxPriceInternational: response.data.max_price_international || 800,
          instantAlerts: response.data.instant_alerts !== false,
          weeklyDigest: response.data.weekly_digest || false
        }
      }));
    } catch (error) {
      console.error('Error loading preferences:', error);
    }
  };

  const toggleDestination = (code) => {
    setPreferences(prev => ({
      ...prev,
      favoriteDestinations: prev.favoriteDestinations.includes(code)
        ? prev.favoriteDestinations.filter(d => d !== code)
        : [...prev.favoriteDestinations, code].slice(0, 10) // Max 10
    }));
  };

  const toggleTravelType = (id) => {
    setPreferences(prev => ({
      ...prev,
      travelTypes: prev.travelTypes.includes(id)
        ? prev.travelTypes.filter(t => t !== id)
        : [...prev.travelTypes, id]
    }));
  };

  const updateAlertSetting = (key, value) => {
    setPreferences(prev => ({
      ...prev,
      alertSettings: {
        ...prev.alertSettings,
        [key]: value
      }
    }));
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      // Update user profile
      await userAPI.updateMe({
        favorite_destinations: preferences.favoriteDestinations,
        travel_types: preferences.travelTypes
      });
      
      // Update alert preferences
      await userAPI.updateAlertPreferences({
        min_discount_percentage: preferences.alertSettings.minDiscount,
        max_price_europe: preferences.alertSettings.maxPriceEurope,
        max_price_international: preferences.alertSettings.maxPriceInternational,
        instant_alerts: preferences.alertSettings.instantAlerts,
        weekly_digest: preferences.alertSettings.weeklyDigest
      });
      
      toast.success('Préférences sauvegardées !');
      navigate('/dashboard');
    } catch (error) {
      toast.error('Erreur lors de la sauvegarde');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between py-4">
            <div className="flex items-center space-x-4">
              <Link to="/dashboard" className="text-gray-600 hover:text-gray-900">
                <ChevronLeft className="h-6 w-6" />
              </Link>
              <h1 className="text-2xl font-bold text-gray-900">Mes préférences</h1>
            </div>
            
            <button
              onClick={handleSave}
              disabled={loading}
              className="flex items-center px-6 py-2 bg-blue-600 text-white rounded-lg 
                       font-semibold hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              {loading ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" />
              ) : (
                <>
                  <Save className="h-5 w-5 mr-2" />
                  Sauvegarder
                </>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Tabs */}
      <div className="bg-white border-b">
        <div className="container mx-auto px-4">
          <div className="flex space-x-8">
            <button
              onClick={() => setActiveTab('destinations')}
              className={`py-4 border-b-2 font-medium transition-colors ${
                activeTab === 'destinations' 
                  ? 'border-blue-600 text-blue-600' 
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <Heart className="h-5 w-5 inline mr-2" />
              Destinations
            </button>
            <button
              onClick={() => setActiveTab('alerts')}
              className={`py-4 border-b-2 font-medium transition-colors ${
                activeTab === 'alerts' 
                  ? 'border-blue-600 text-blue-600' 
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <Bell className="h-5 w-5 inline mr-2" />
              Alertes
            </button>
            <button
              onClick={() => setActiveTab('travel')}
              className={`py-4 border-b-2 font-medium transition-colors ${
                activeTab === 'travel' 
                  ? 'border-blue-600 text-blue-600' 
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <Globe className="h-5 w-5 inline mr-2" />
              Type de voyage
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <main className="container mx-auto px-4 py-8">
        {/* Destinations Tab */}
        {activeTab === 'destinations' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-4xl mx-auto"
          >
            <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
              <h2 className="text-xl font-bold text-gray-900 mb-2">Destinations favorites</h2>
              <p className="text-gray-600 mb-6">
                Sélectionnez jusqu'à 10 destinations pour recevoir des alertes prioritaires
              </p>
              
              {preferences.favoriteDestinations.length > 0 && (
                <div className="mb-6 p-4 bg-blue-50 rounded-lg">
                  <p className="text-sm text-blue-700">
                    {preferences.favoriteDestinations.length}/10 destinations sélectionnées
                  </p>
                </div>
              )}
              
              {[...new Set(DESTINATIONS.map(d => d.region))].map(region => (
                <div key={region} className="mb-8">
                  <h3 className="font-semibold text-gray-700 mb-3">{region}</h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {DESTINATIONS.filter(d => d.region === region).map(dest => (
                      <button
                        key={dest.code}
                        onClick={() => toggleDestination(dest.code)}
                        disabled={!preferences.favoriteDestinations.includes(dest.code) && 
                                 preferences.favoriteDestinations.length >= 10}
                        className={`p-4 rounded-lg border-2 transition-all text-left
                          ${preferences.favoriteDestinations.includes(dest.code)
                            ? 'border-blue-500 bg-blue-50 text-blue-700'
                            : 'border-gray-200 hover:border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed'}`}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="font-semibold">{dest.name}</div>
                            <div className="text-sm opacity-75">{dest.code}</div>
                          </div>
                          <span className="text-2xl">{dest.emoji}</span>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Alerts Tab */}
        {activeTab === 'alerts' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-4xl mx-auto"
          >
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-6">Paramètres d'alertes</h2>
              
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Réduction minimale : {preferences.alertSettings.minDiscount}%
                  </label>
                  <input
                    type="range"
                    min="10"
                    max="90"
                    value={preferences.alertSettings.minDiscount}
                    onChange={(e) => updateAlertSetting('minDiscount', parseInt(e.target.value))}
                    className="w-full"
                  />
                  <p className="text-sm text-gray-500 mt-1">
                    Ne recevoir que les offres avec au moins {preferences.alertSettings.minDiscount}% de réduction
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Prix max Europe
                    </label>
                    <div className="relative">
                      <Euro className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                      <input
                        type="number"
                        value={preferences.alertSettings.maxPriceEurope}
                        onChange={(e) => updateAlertSetting('maxPriceEurope', parseInt(e.target.value))}
                        className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg 
                                 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Prix max International
                    </label>
                    <div className="relative">
                      <Euro className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                      <input
                        type="number"
                        value={preferences.alertSettings.maxPriceInternational}
                        onChange={(e) => updateAlertSetting('maxPriceInternational', parseInt(e.target.value))}
                        className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg 
                                 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <label className="flex items-center p-4 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100">
                    <input
                      type="checkbox"
                      checked={preferences.alertSettings.instantAlerts}
                      onChange={(e) => updateAlertSetting('instantAlerts', e.target.checked)}
                      className="w-5 h-5 text-blue-600 rounded mr-4"
                    />
                    <div>
                      <p className="font-semibold text-gray-900">Alertes instantanées</p>
                      <p className="text-sm text-gray-600">
                        Recevez une notification dès qu'une offre est détectée
                      </p>
                    </div>
                  </label>

                  <label className="flex items-center p-4 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100">
                    <input
                      type="checkbox"
                      checked={preferences.alertSettings.weeklyDigest}
                      onChange={(e) => updateAlertSetting('weeklyDigest', e.target.checked)}
                      className="w-5 h-5 text-blue-600 rounded mr-4"
                    />
                    <div>
                      <p className="font-semibold text-gray-900">Résumé hebdomadaire</p>
                      <p className="text-sm text-gray-600">
                        Recevez un récapitulatif des meilleures offres chaque semaine
                      </p>
                    </div>
                  </label>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Travel Types Tab */}
        {activeTab === 'travel' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-4xl mx-auto"
          >
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-2">Types de voyage</h2>
              <p className="text-gray-600 mb-6">
                Nous personnaliserons nos recommandations selon vos habitudes de voyage
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {TRAVEL_TYPES.map(type => {
                  const Icon = type.icon;
                  const isSelected = preferences.travelTypes.includes(type.id);
                  
                  return (
                    <button
                      key={type.id}
                      onClick={() => toggleTravelType(type.id)}
                      className={`p-6 rounded-xl border-2 transition-all text-left
                        ${isSelected
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'}`}
                    >
                      <div className="flex items-start space-x-4">
                        <div className={`p-3 rounded-lg ${type.color}`}>
                          <Icon className="w-6 h-6" />
                        </div>
                        <div className="flex-1">
                          <h5 className="font-semibold text-gray-900">{type.name}</h5>
                          <p className="text-sm text-gray-600 mt-1">{type.description}</p>
                        </div>
                        {isSelected && (
                          <Check className="w-5 h-5 text-blue-600 mt-1" />
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>

              <div className="mt-8 p-4 bg-yellow-50 rounded-lg">
                <div className="flex items-start space-x-3">
                  <Settings className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                  <div className="text-sm">
                    <p className="font-semibold text-yellow-900">
                      Personnalisation intelligente
                    </p>
                    <p className="text-yellow-700 mt-1">
                      Nous analyserons vos clics et préférences pour affiner automatiquement 
                      vos alertes au fil du temps.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </main>
    </div>
  );
};

export default Preferences;