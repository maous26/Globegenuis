import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Plane, Filter, MapPin, Calendar, TrendingDown,
  Clock, AlertCircle, ChevronDown, Star, ChevronRight,
  Euro, Loader, Globe, ArrowRight, X
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { flightAPI } from '../services/api';
import toast from 'react-hot-toast';

const MOCK_DEALS = [
  {
    id: 1,
    route: { origin: 'CDG', destination: 'JFK', origin_city: 'Paris', destination_city: 'New York' },
    deal_price: 189,
    normal_price: 890,
    discount_percentage: 78,
    is_error_fare: true,
    airline: 'Air France',
    departure_dates: ['2024-03-15', '2024-03-22', '2024-03-29'],
    expires_at: new Date(Date.now() + 24 * 60 * 60 * 1000),
    confidence_score: 95
  },
  {
    id: 2,
    route: { origin: 'CDG', destination: 'BKK', origin_city: 'Paris', destination_city: 'Bangkok' },
    deal_price: 380,
    normal_price: 750,
    discount_percentage: 49,
    is_error_fare: false,
    airline: 'Qatar Airways',
    departure_dates: ['2024-04-10', '2024-04-17', '2024-04-24'],
    expires_at: new Date(Date.now() + 48 * 60 * 60 * 1000),
    confidence_score: 88
  },
  {
    id: 3,
    route: { origin: 'CDG', destination: 'LAX', origin_city: 'Paris', destination_city: 'Los Angeles' },
    deal_price: 299,
    normal_price: 1200,
    discount_percentage: 75,
    is_error_fare: true,
    airline: 'United Airlines',
    departure_dates: ['2024-05-01', '2024-05-08'],
    expires_at: new Date(Date.now() + 6 * 60 * 60 * 1000),
    confidence_score: 92
  }
];

const Deals = () => {
  const { user } = useAuth();
  const [deals, setDeals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    origin: '',
    destination: '',
    maxPrice: '',
    minDiscount: 30,
    showErrorFares: true
  });
  const [showFilters, setShowFilters] = useState(false);
  const [sortBy, setSortBy] = useState('discount');
  const [selectedDeal, setSelectedDeal] = useState(null);

  useEffect(() => {
    fetchDeals();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters]);

  const fetchDeals = async () => {
    setLoading(true);
    try {
      // For now, use mock data
      setTimeout(() => {
        setDeals(MOCK_DEALS);
        setLoading(false);
      }, 1000);
      
      // Real API call (uncomment when backend is ready)
      // const response = await flightAPI.getDeals({
      //   origin: filters.origin,
      //   destination: filters.destination,
      //   min_discount: filters.minDiscount
      // });
      // setDeals(response.data);
    } catch (error) {
      console.error('Error fetching deals:', error);
      toast.error('Erreur lors du chargement des offres');
    } finally {
      // setLoading(false);
    }
  };

  const handleSort = (criteria) => {
    setSortBy(criteria);
    const sorted = [...deals].sort((a, b) => {
      switch (criteria) {
        case 'discount':
          return b.discount_percentage - a.discount_percentage;
        case 'price':
          return a.deal_price - b.deal_price;
        case 'expires':
          return new Date(a.expires_at) - new Date(b.expires_at);
        default:
          return 0;
      }
    });
    setDeals(sorted);
  };

  const formatTimeRemaining = (expiresAt) => {
    const now = new Date();
    const expires = new Date(expiresAt);
    const diff = expires - now;
    
    if (diff < 0) return 'Expiré';
    
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    if (hours > 24) {
      const days = Math.floor(hours / 24);
      return `${days}j restants`;
    }
    
    return `${hours}h ${minutes}m`;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-40">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between py-4">
            <Link to="/dashboard" className="flex items-center space-x-2">
              <Plane className="h-8 w-8 text-blue-600" />
              <span className="text-2xl font-bold text-gray-900">GlobeGenius</span>
            </Link>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="flex items-center space-x-2 px-4 py-2 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              >
                <Filter className="h-5 w-5" />
                <span className="hidden md:inline">Filtres</span>
                {showFilters ? <ChevronDown className="h-4 w-4 rotate-180 transition-transform" /> : <ChevronDown className="h-4 w-4 transition-transform" />}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-12">
        <div className="container mx-auto px-4">
          <h1 className="text-4xl font-bold mb-4">Offres en cours</h1>
          <p className="text-xl opacity-90 mb-6">
            {deals.length} opportunités détectées • Économisez jusqu'à 90% sur vos vols
          </p>
          
          {/* Sort Options */}
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => handleSort('discount')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                sortBy === 'discount' 
                  ? 'bg-white text-blue-600' 
                  : 'bg-white/20 text-white hover:bg-white/30'
              }`}
            >
              Plus grandes réductions
            </button>
            <button
              onClick={() => handleSort('price')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                sortBy === 'price' 
                  ? 'bg-white text-blue-600' 
                  : 'bg-white/20 text-white hover:bg-white/30'
              }`}
            >
              Prix le plus bas
            </button>
            <button
              onClick={() => handleSort('expires')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                sortBy === 'expires' 
                  ? 'bg-white text-blue-600' 
                  : 'bg-white/20 text-white hover:bg-white/30'
              }`}
            >
              Expire bientôt
            </button>
          </div>
        </div>
      </section>

      {/* Filters (collapsible) */}
      <AnimatePresence>
        {showFilters && (
          <motion.section
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="bg-white border-b border-gray-200 overflow-hidden"
          >
            <div className="container mx-auto px-4 py-6">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Départ
                  </label>
                  <div className="relative">
                    <MapPin className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Code aéroport"
                      value={filters.origin}
                      onChange={(e) => setFilters({ ...filters, origin: e.target.value.toUpperCase() })}
                      className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Arrivée
                  </label>
                  <div className="relative">
                    <MapPin className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Code aéroport"
                      value={filters.destination}
                      onChange={(e) => setFilters({ ...filters, destination: e.target.value.toUpperCase() })}
                      className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Prix max
                  </label>
                  <div className="relative">
                    <Euro className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                    <input
                      type="number"
                      placeholder="Ex: 500"
                      value={filters.maxPrice}
                      onChange={(e) => setFilters({ ...filters, maxPrice: e.target.value })}
                      className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Réduction min: {filters.minDiscount}%
                  </label>
                  <input
                    type="range"
                    min="20"
                    max="80"
                    value={filters.minDiscount}
                    onChange={(e) => setFilters({ ...filters, minDiscount: parseInt(e.target.value) })}
                    className="w-full"
                  />
                </div>
              </div>
              
              <div className="mt-4 flex items-center justify-between">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={filters.showErrorFares}
                    onChange={(e) => setFilters({ ...filters, showErrorFares: e.target.checked })}
                    className="rounded text-blue-600 mr-2"
                  />
                  <span className="text-sm text-gray-700">Afficher les erreurs de prix</span>
                </label>
                
                <button
                  onClick={() => setFilters({
                    origin: '',
                    destination: '',
                    maxPrice: '',
                    minDiscount: 30,
                    showErrorFares: true
                  })}
                  className="text-sm text-blue-600 hover:text-blue-700"
                >
                  Réinitialiser les filtres
                </button>
              </div>
            </div>
          </motion.section>
        )}
      </AnimatePresence>

      {/* Deals Grid */}
      <main className="container mx-auto px-4 py-8">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader className="h-8 w-8 text-blue-600 animate-spin" />
          </div>
        ) : deals.length === 0 ? (
          <div className="text-center py-20">
            <Globe className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Aucune offre trouvée</h3>
            <p className="text-gray-600">Modifiez vos filtres ou revenez plus tard</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {deals.map((deal, index) => (
              <motion.div
                key={deal.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
                onClick={() => setSelectedDeal(deal)}
                className="bg-white rounded-xl shadow-lg hover:shadow-xl transition-all cursor-pointer overflow-hidden group"
              >
                {/* Deal Header */}
                <div className="relative p-6 bg-gradient-to-r from-blue-500 to-indigo-500 text-white">
                  {deal.is_error_fare && (
                    <div className="absolute top-4 right-4 px-3 py-1 bg-red-500 rounded-full text-xs font-bold animate-pulse">
                      ERREUR DE PRIX
                    </div>
                  )}
                  
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <div className="text-3xl font-bold">{deal.route.origin} → {deal.route.destination}</div>
                      <div className="text-blue-100 mt-1">
                        {deal.route.origin_city} → {deal.route.destination_city}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4 text-sm">
                    <div className="flex items-center">
                      <Plane className="h-4 w-4 mr-1" />
                      {deal.airline}
                    </div>
                    <div className="flex items-center">
                      <Clock className="h-4 w-4 mr-1" />
                      {formatTimeRemaining(deal.expires_at)}
                    </div>
                  </div>
                </div>
                
                {/* Deal Body */}
                <div className="p-6">
                  <div className="flex justify-between items-end mb-4">
                    <div>
                      <div className="text-4xl font-bold text-gray-900">{deal.deal_price}€</div>
                      <div className="text-gray-500 line-through">{deal.normal_price}€</div>
                    </div>
                    <div className="text-right">
                      <div className="text-3xl font-bold text-green-600">
                        -{Math.round(deal.discount_percentage)}%
                      </div>
                      <div className="text-sm text-gray-600">
                        Économie: {deal.normal_price - deal.deal_price}€
                      </div>
                    </div>
                  </div>
                  
                  {/* Dates */}
                  <div className="mb-4">
                    <div className="text-sm text-gray-600 mb-2">Dates disponibles:</div>
                    <div className="flex flex-wrap gap-2">
                      {deal.departure_dates.slice(0, 3).map((date, i) => (
                        <span key={i} className="px-3 py-1 bg-gray-100 rounded-full text-sm">
                          {new Date(date).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })}
                        </span>
                      ))}
                      {deal.departure_dates.length > 3 && (
                        <span className="px-3 py-1 bg-gray-100 rounded-full text-sm text-gray-600">
                          +{deal.departure_dates.length - 3} autres
                        </span>
                      )}
                    </div>
                  </div>
                  
                  {/* Confidence Score */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div className="flex items-center">
                        {[...Array(5)].map((_, i) => (
                          <Star 
                            key={i} 
                            className={`h-4 w-4 ${
                              i < Math.floor(deal.confidence_score / 20) 
                                ? 'fill-yellow-400 text-yellow-400' 
                                : 'text-gray-300'
                            }`} 
                          />
                        ))}
                      </div>
                      <span className="text-sm text-gray-600">
                        Fiabilité: {deal.confidence_score}%
                      </span>
                    </div>
                    
                    <ArrowRight className="h-5 w-5 text-blue-600 group-hover:translate-x-1 transition-transform" />
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </main>

      {/* Deal Detail Modal */}
      <AnimatePresence>
        {selectedDeal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
            onClick={() => setSelectedDeal(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
            >
              <div className="relative p-8">
                <button
                  onClick={() => setSelectedDeal(null)}
                  className="absolute top-4 right-4 p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <X className="h-6 w-6" />
                </button>
                
                <h2 className="text-3xl font-bold text-gray-900 mb-2">
                  {selectedDeal.route.origin_city} → {selectedDeal.route.destination_city}
                </h2>
                
                <div className="flex items-center space-x-4 text-gray-600 mb-6">
                  <span>{selectedDeal.airline}</span>
                  <span>•</span>
                  <span className="flex items-center">
                    <Clock className="h-4 w-4 mr-1" />
                    {formatTimeRemaining(selectedDeal.expires_at)}
                  </span>
                </div>
                
                {selectedDeal.is_error_fare && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
                    <div className="flex items-start">
                      <AlertCircle className="h-5 w-5 text-red-600 mr-2 flex-shrink-0 mt-0.5" />
                      <div>
                        <p className="font-semibold text-red-900">Erreur de prix détectée !</p>
                        <p className="text-sm text-red-700 mt-1">
                          Ce tarif est anormalement bas et pourrait être corrigé rapidement. 
                          Réservez immédiatement si vous êtes intéressé.
                        </p>
                      </div>
                    </div>
                  </div>
                )}
                
                <div className="grid grid-cols-2 gap-6 mb-6">
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Prix de l'offre</div>
                    <div className="text-4xl font-bold text-gray-900">{selectedDeal.deal_price}€</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Prix normal</div>
                    <div className="text-2xl text-gray-500 line-through">{selectedDeal.normal_price}€</div>
                    <div className="text-green-600 font-semibold">
                      Économie: {selectedDeal.normal_price - selectedDeal.deal_price}€
                    </div>
                  </div>
                </div>
                
                <div className="mb-6">
                  <h3 className="font-semibold text-gray-900 mb-3">Dates disponibles</h3>
                  <div className="grid grid-cols-3 gap-3">
                    {selectedDeal.departure_dates.map((date, i) => (
                      <div key={i} className="p-3 bg-gray-50 rounded-lg text-center">
                        <div className="text-sm text-gray-600">
                          {new Date(date).toLocaleDateString('fr-FR', { weekday: 'short' })}
                        </div>
                        <div className="font-semibold">
                          {new Date(date).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' })}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Score de fiabilité</div>
                    <div className="flex items-center space-x-2">
                      <div className="flex items-center">
                        {[...Array(5)].map((_, i) => (
                          <Star 
                            key={i} 
                            className={`h-5 w-5 ${
                              i < Math.floor(selectedDeal.confidence_score / 20) 
                                ? 'fill-yellow-400 text-yellow-400' 
                                : 'text-gray-300'
                            }`} 
                          />
                        ))}
                      </div>
                      <span className="font-semibold">{selectedDeal.confidence_score}%</span>
                    </div>
                  </div>
                </div>
                
                <div className="flex space-x-4">
                  <button className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors flex items-center justify-center">
                    Voir l'offre
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </button>
                  <button 
                    onClick={() => {
                      // Add to saved deals
                      toast.success('Offre sauvegardée !');
                      setSelectedDeal(null);
                    }}
                    className="px-6 py-3 bg-gray-100 text-gray-700 rounded-lg font-semibold hover:bg-gray-200 transition-colors"
                  >
                    Sauvegarder
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default Deals;