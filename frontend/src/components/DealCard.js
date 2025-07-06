import React, { useState } from 'react';
import { 
  Clock, 
  MapPin, 
  TrendingDown, 
  AlertCircle, 
  ChevronRight,
  Calendar,
  Plane,
  Star
} from 'lucide-react';

const DealCard = ({ deal }) => {
  const [isHovered, setIsHovered] = useState(false);
  
  // Mock data structure for the deal
  const mockDeal = deal || {
    id: 1,
    route: {
      origin: 'CDG',
      destination: 'JFK',
      originCity: 'Paris',
      destinationCity: 'New York'
    },
    dealPrice: 189,
    normalPrice: 890,
    discountPercentage: 79,
    isErrorFare: true,
    confidenceScore: 85,
    expiresAt: new Date(Date.now() + 4 * 60 * 60 * 1000), // 4 hours from now
    departureDate: new Date(Date.now() + 60 * 24 * 60 * 60 * 1000), // 60 days from now
    airline: 'Air France',
    savings: 701
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

  const formatDate = (date) => {
    return new Date(date).toLocaleDateString('fr-FR', { 
      day: 'numeric', 
      month: 'short',
      year: 'numeric'
    });
  };

  return (
    <div 
      className={`bg-white rounded-xl shadow-sm hover:shadow-xl transition-all duration-300 
                  overflow-hidden cursor-pointer transform ${isHovered ? 'scale-[1.02]' : ''}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Deal Header Gradient */}
      <div className={`h-2 bg-gradient-to-r ${getDealTypeColor(mockDeal.discountPercentage)}`} />
      
      <div className="p-6">
        {/* Deal Type & Time */}
        <div className="flex items-center justify-between mb-4">
          <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
            getDealTypeLabel(mockDeal.discountPercentage, mockDeal.isErrorFare).color
          }`}>
            {getDealTypeLabel(mockDeal.discountPercentage, mockDeal.isErrorFare).text}
          </span>
          <span className="text-sm text-gray-500 flex items-center">
            <Clock className="h-4 w-4 mr-1" />
            {formatTimeRemaining(mockDeal.expiresAt)}
          </span>
        </div>
        
        {/* Route */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-lg font-bold text-gray-900">
              {mockDeal.route.origin} → {mockDeal.route.destination}
            </h3>
            <Plane className="h-5 w-5 text-gray-400" />
          </div>
          <p className="text-sm text-gray-600 flex items-center">
            <MapPin className="h-4 w-4 mr-1" />
            {mockDeal.route.originCity} → {mockDeal.route.destinationCity}
          </p>
          <p className="text-sm text-gray-500 flex items-center mt-1">
            <Calendar className="h-4 w-4 mr-1" />
            Départ: {formatDate(mockDeal.departureDate)}
          </p>
        </div>
        
        {/* Prices */}
        <div className="mb-4">
          <div className="flex items-baseline">
            <span className="text-3xl font-bold text-gray-900">
              {Math.round(mockDeal.dealPrice)}€
            </span>
            <span className="ml-2 text-xl text-gray-400 line-through">
              {Math.round(mockDeal.normalPrice)}€
            </span>
            <span className="ml-3 bg-green-100 text-green-800 px-2 py-1 rounded text-sm font-semibold">
              -{Math.round(mockDeal.discountPercentage)}%
            </span>
          </div>
          <p className="text-sm text-green-600 mt-1 flex items-center">
            <TrendingDown className="h-4 w-4 mr-1" />
            Économie de {Math.round(mockDeal.savings)}€
          </p>
        </div>
        
        {/* Airline & Confidence */}
        <div className="flex items-center justify-between mb-4 text-sm">
          <span className="text-gray-600">{mockDeal.airline}</span>
          <div className="flex items-center">
            <Star className="h-4 w-4 text-yellow-400 mr-1" />
            <span className="text-gray-600">Fiabilité: {mockDeal.confidenceScore}%</span>
          </div>
        </div>
        
        {/* Warning for Error Fares */}
        {mockDeal.isErrorFare && (
          <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-xs text-yellow-800 flex items-start">
              <AlertCircle className="h-4 w-4 mr-1 flex-shrink-0 mt-0.5" />
              <span>
                Erreur de prix détectée ! Réservez rapidement, ce tarif peut être corrigé à tout moment.
              </span>
            </p>
          </div>
        )}
        
        {/* CTA Button */}
        <button className={`w-full bg-gradient-to-r ${getDealTypeColor(mockDeal.discountPercentage)} 
                           text-white py-3 rounded-lg font-semibold transition-all 
                           flex items-center justify-center group`}>
          <span>Voir les détails</span>
          <ChevronRight className="h-5 w-5 ml-1 transform group-hover:translate-x-1 transition-transform" />
        </button>
      </div>
    </div>
  );
};

// Example usage with multiple deals
const DealsGrid = () => {
  const sampleDeals = [
    {
      id: 1,
      route: { origin: 'CDG', destination: 'NYC', originCity: 'Paris', destinationCity: 'New York' },
      dealPrice: 189,
      normalPrice: 890,
      discountPercentage: 79,
      isErrorFare: true,
      confidenceScore: 92,
      expiresAt: new Date(Date.now() + 4 * 60 * 60 * 1000),
      departureDate: new Date('2025-03-15'),
      airline: 'Air France',
      savings: 701
    },
    {
      id: 2,
      route: { origin: 'LYS', destination: 'BKK', originCity: 'Lyon', destinationCity: 'Bangkok' },
      dealPrice: 349,
      normalPrice: 1150,
      discountPercentage: 70,
      isErrorFare: false,
      confidenceScore: 88,
      expiresAt: new Date(Date.now() + 8 * 60 * 60 * 1000),
      departureDate: new Date('2025-04-20'),
      airline: 'Thai Airways',
      savings: 801
    },
    {
      id: 3,
      route: { origin: 'MRS', destination: 'LIS', originCity: 'Marseille', destinationCity: 'Lisbonne' },
      dealPrice: 39,
      normalPrice: 180,
      discountPercentage: 78,
      isErrorFare: false,
      confidenceScore: 85,
      expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000),
      departureDate: new Date('2025-02-28'),
      airline: 'TAP Portugal',
      savings: 141
    }
  ];

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <h2 className="text-2xl font-bold mb-6">Derniers Deals Détectés</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {sampleDeals.map(deal => (
          <DealCard key={deal.id} deal={deal} />
        ))}
      </div>
    </div>
  );
};

export default DealsGrid;