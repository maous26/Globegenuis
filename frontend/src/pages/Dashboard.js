// frontend/src/pages/Dashboard.js
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  TrendingDown, 
  Bell, 
  Settings, 
  Clock, 
  MapPin,
  AlertCircle,
  Star,
  Filter,
  RefreshCw,
  ChevronRight,
  Zap,
  LogOut
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { flightAPI } from '../services/api';
import toast from 'react-hot-toast';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const [deals, setDeals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState('all');
  const [stats, setStats] = useState({
    totalSavings: 0,
    dealsFound: 0,
    avgDiscount: 0
  });

  useEffect(() => {
    fetchDeals();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter]);

  const fetchDeals = async () => {
    try {
      setLoading(true);
      
      // Fetch deals based on filter
      const params = {};
      if (filter === 'errors') {
        params.min_discount = 70;
      } else if (filter === 'departures' && user?.home_airports?.length > 0) {
        params.origin = user.home_airports[0];
      }
      
      const response = await flightAPI.getDeals(params);
      const dealsData = response.data || [];
      
      setDeals(dealsData);
      
      // Calculate stats
      if (dealsData.length > 0) {
        const totalSavings = dealsData.reduce((sum, deal) => 
          sum + (deal.normal_price - deal.deal_price), 0
        );
        const avgDiscount = dealsData.reduce((sum, deal) => 
          sum + deal.discount_percentage, 0
        ) / dealsData.length;
        
        setStats({
          totalSavings: Math.round(totalSavings),
          dealsFound: dealsData.length,
          avgDiscount: Math.round(avgDiscount)
        });
      }
    } catch (error) {
      console.error('Error fetching deals:', error);
      toast.error('Erreur lors du chargement des deals');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchDeals();
    setRefreshing(false);
    toast.success('Deals actualisés !');
  };

  const getDealTypeColor = (discount) => {
    if (discount >= 70) return 'from-red-500 to-pink-500';
    if (discount >= 50) return 'from-blue-500 to-indigo-500';
    return 'from-green-500 to-emerald-500';
  };

  const getDealTypeLabel = (discount, isErrorFare) => {
    if (isErrorFare) return { text: 'Erreur de prix', color: 'bg-red-100 text-red-800' };
    if (discount >= 70) return { text: 'Prix cassé', color: 'bg-blue-100 text-blue-800' };
    if (discount >= 50) return { text: 'Super deal', color: 'bg-green-100 text-green-800' };
    return { text: 'Bonne affaire', color: 'bg-gray-100 text-gray-800' };
  };

  const formatTimeRemaining = (expiresAt) => {
    if (!expiresAt) return 'Durée limitée';
    
    const now = new Date();
    const expires = new Date(expiresAt);
    const hoursRemaining = Math.floor((expires - now) / (1000 * 60 * 60));
    
    if (hoursRemaining < 1) return 'Expire bientôt !';
    if (hoursRemaining < 24) return `${hoursRemaining}h restantes`;
    const daysRemaining = Math.floor(hoursRemaining / 24);
    return `${daysRemaining}j restants`;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="container mx-auto px-4 py-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Bonjour {user?.first_name || user?.email?.split('@')[0] || 'Voyageur'} ! 👋
              </h1>
              <p className="text-gray-600 mt-1">
                Voici les meilleures offres détectées pour vous aujourd'hui
              </p>
            </div>
            
            <div className="flex items-center space-x-4 mt-4 md:mt-0">
              <Link 
                to="/profile" 
                className="flex items-center px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition"
              >
                <Settings className="h-5 w-5 mr-2" />
                Préférences
              </Link>
              <button
                onClick={logout}
                className="flex items-center px-3 py-2 text-red-600 bg-red-50 rounded-lg hover:bg-red-100 transition"
              >
                <LogOut className="h-5 w-5 mr-2" />
                Déconnexion
              </button>
              <button
                onClick={handleRefresh}
                disabled={refreshing}
                className="flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
              >
                <RefreshCw className={`h-5 w-5 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
                Actualiser
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Stats Cards */}
      <section className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-xl shadow-sm p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Économies potentielles</p>
                <p className="text-3xl font-bold text-gray-900">{stats.totalSavings}€</p>
              </div>
              <div className="h-12 w-12 bg-green-100 rounded-full flex items-center justify-center">
                <TrendingDown className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </motion.div>
          
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white rounded-xl shadow-sm p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Deals actifs</p>
                <p className="text-3xl font-bold text-gray-900">{stats.dealsFound}</p>
              </div>
              <div className="h-12 w-12 bg-blue-100 rounded-full flex items-center justify-center">
                <Zap className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </motion.div>
          
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white rounded-xl shadow-sm p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Réduction moyenne</p>
                <p className="text-3xl font-bold text-gray-900">{stats.avgDiscount}%</p>
              </div>
              <div className="h-12 w-12 bg-purple-100 rounded-full flex items-center justify-center">
                <Star className="h-6 w-6 text-purple-600" />
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Filters */}
      <section className="container mx-auto px-4 pb-6">
        <div className="flex items-center space-x-4">
          <Filter className="h-5 w-5 text-gray-500" />
          <button
            onClick={() => setFilter('all')}
            className={`px-4 py-2 rounded-lg font-medium transition ${
              filter === 'all' 
                ? 'bg-indigo-600 text-white' 
                : 'bg-white text-gray-700 hover:bg-gray-100'
            }`}
          >
            Tous les deals
          </button>
          <button
            onClick={() => setFilter('errors')}
            className={`px-4 py-2 rounded-lg font-medium transition ${
              filter === 'errors' 
                ? 'bg-indigo-600 text-white' 
                : 'bg-white text-gray-700 hover:bg-gray-100'
            }`}
          >
            Erreurs de prix
          </button>
          <button
            onClick={() => setFilter('departures')}
            className={`px-4 py-2 rounded-lg font-medium transition ${
              filter === 'departures' 
                ? 'bg-indigo-600 text-white' 
                : 'bg-white text-gray-700 hover:bg-gray-100'
            }`}
          >
            Mes aéroports
          </button>
        </div>
      </section>

      {/* Deals Grid */}
      <section className="container mx-auto px-4 pb-12">
        {loading ? (
          <div className="flex justify-center items-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
          </div>
        ) : deals.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm p-12 text-center">
            <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Aucun deal trouvé
            </h3>
            <p className="text-gray-600">
              Revenez plus tard ou ajustez vos préférences pour voir plus d'offres
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {deals.map((deal, index) => (
              <motion.div
                key={deal.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-white rounded-xl shadow-sm hover:shadow-lg transition-shadow cursor-pointer overflow-hidden"
              >
                {/* Deal Header */}
                <div className={`h-2 bg-gradient-to-r ${getDealTypeColor(deal.discount_percentage)}`} />
                
                <div className="p-6">
                  {/* Deal Type & Time */}
                  <div className="flex items-center justify-between mb-4">
                    <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                      getDealTypeLabel(deal.discount_percentage, deal.is_error_fare).color
                    }`}>
                      {getDealTypeLabel(deal.discount_percentage, deal.is_error_fare).text}
                    </span>
                    <span className="text-sm text-gray-500 flex items-center">
                      <Clock className="h-4 w-4 mr-1" />
                      {formatTimeRemaining(deal.expires_at)}
                    </span>
                  </div>
                  
                  {/* Route */}
                  <div className="mb-4">
                    <h3 className="text-lg font-bold text-gray-900 mb-1">
                      {deal.route.origin} → {deal.route.destination}
                    </h3>
                    <p className="text-sm text-gray-600 flex items-center">
                      <MapPin className="h-4 w-4 mr-1" />
                      Direct • Aller-retour
                    </p>
                  </div>
                  
                  {/* Prices */}
                  <div className="mb-4">
                    <div className="flex items-baseline">
                      <span className="text-3xl font-bold text-gray-900">
                        {Math.round(deal.deal_price)}€
                      </span>
                      <span className="ml-2 text-xl text-gray-400 line-through">
                        {Math.round(deal.normal_price)}€
                      </span>
                      <span className="ml-3 bg-green-100 text-green-800 px-2 py-1 rounded text-sm font-semibold">
                        -{Math.round(deal.discount_percentage)}%
                      </span>
                    </div>
                    <p className="text-sm text-green-600 mt-1">
                      Économie de {Math.round(deal.normal_price - deal.deal_price)}€
                    </p>
                  </div>
                  
                  {/* Confidence Score */}
                  {deal.confidence_score && (
                    <div className="mb-4">
                      <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
                        <span>Fiabilité du deal</span>
                        <span>{Math.round(deal.confidence_score)}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-indigo-600 h-2 rounded-full"
                          style={{ width: `${deal.confidence_score}%` }}
                        />
                      </div>
                    </div>
                  )}
                  
                  {/* CTA Button */}
                  <button className="w-full bg-indigo-600 text-white py-3 rounded-lg font-semibold hover:bg-indigo-700 transition flex items-center justify-center">
                    Voir les détails
                    <ChevronRight className="h-5 w-5 ml-1" />
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </section>

      {/* Alert Preferences Reminder */}
      {user && !user.onboarding_completed && (
        <div className="fixed bottom-6 right-6 bg-white rounded-lg shadow-xl p-6 max-w-sm">
          <div className="flex items-start">
            <Bell className="h-6 w-6 text-indigo-600 mr-3 flex-shrink-0" />
            <div>
              <h4 className="font-semibold text-gray-900 mb-1">
                Complétez votre profil
              </h4>
              <p className="text-sm text-gray-600 mb-3">
                Personnalisez vos alertes pour recevoir les meilleures offres
              </p>
              <Link 
                to="/onboarding"
                className="text-sm text-indigo-600 font-semibold hover:underline"
              >
                Continuer la configuration →
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;