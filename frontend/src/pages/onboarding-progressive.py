import React, { useState } from 'react';
import { 
  Plane, 
  MapPin, 
  Heart, 
  Globe, 
  Bell, 
  CheckCircle,
  ArrowRight,
  ArrowLeft,
  Sparkles,
  TrendingDown,
  Mail
} from 'lucide-react';

const Onboarding = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  
  // Form data state
  const [formData, setFormData] = useState({
    firstName: '',
    homeAirports: [],
    travelTypes: [],
    favoriteDestinations: [],
    alertFrequency: 'instant'
  });

  // Popular airports for quick selection
  const popularAirports = [
    { code: 'CDG', name: 'Paris CDG', city: 'Paris' },
    { code: 'ORY', name: 'Paris Orly', city: 'Paris' },
    { code: 'NCE', name: 'Nice', city: 'Nice' },
    { code: 'LYS', name: 'Lyon', city: 'Lyon' },
    { code: 'MRS', name: 'Marseille', city: 'Marseille' },
    { code: 'TLS', name: 'Toulouse', city: 'Toulouse' },
    { code: 'BOD', name: 'Bordeaux', city: 'Bordeaux' },
    { code: 'NTE', name: 'Nantes', city: 'Nantes' }
  ];

  // Popular destinations
  const popularDestinations = [
    { code: 'NYC', name: 'New York', emoji: '🗽' },
    { code: 'BCN', name: 'Barcelone', emoji: '🏖️' },
    { code: 'LON', name: 'Londres', emoji: '🇬🇧' },
    { code: 'ROM', name: 'Rome', emoji: '🏛️' },
    { code: 'TYO', name: 'Tokyo', emoji: '🗾' },
    { code: 'BKK', name: 'Bangkok', emoji: '🏝️' },
    { code: 'DXB', name: 'Dubaï', emoji: '🌆' },
    { code: 'LAX', name: 'Los Angeles', emoji: '🌴' }
  ];

  const handleNext = async () => {
    setLoading(true);
    
    // Simulate API call
    setTimeout(() => {
      // Validation logic
      let isValid = true;
      let errorMessage = '';
      
      switch (currentStep) {
        case 1:
          // Step 1 is just welcome, no validation needed
          break;
          
        case 2:
          if (!formData.firstName.trim()) {
            errorMessage = 'Veuillez entrer votre prénom';
            isValid = false;
          } else if (formData.homeAirports.length === 0) {
            errorMessage = 'Veuillez sélectionner au moins un aéroport';
            isValid = false;
          }
          break;
          
        case 3:
          if (formData.travelTypes.length === 0) {
            errorMessage = 'Veuillez sélectionner au moins un type de voyage';
            isValid = false;
          }
          break;
          
        case 4:
          if (formData.favoriteDestinations.length === 0) {
            errorMessage = 'Veuillez sélectionner au moins une destination';
            isValid = false;
          }
          break;
      }
      
      if (!isValid) {
        alert(errorMessage);
        setLoading(false);
        return;
      }
      
      if (currentStep === 5) {
        // Onboarding complete!
        alert('🎉 Profil complété avec succès !');
        console.log('Onboarding data:', formData);
      } else {
        setCurrentStep(currentStep + 1);
      }
      
      setLoading(false);
    }, 500);
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return <StepWelcome />;
      case 2:
        return <StepProfile formData={formData} setFormData={setFormData} popularAirports={popularAirports} />;
      case 3:
        return <StepTravelTypes formData={formData} setFormData={setFormData} />;
      case 4:
        return <StepDestinations formData={formData} setFormData={setFormData} popularDestinations={popularDestinations} />;
      case 5:
        return <StepNotifications formData={formData} setFormData={setFormData} />;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-2xl">
        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm text-gray-600">Étape {currentStep} sur 5</span>
            <span className="text-sm text-gray-600">{Math.round((currentStep / 5) * 100)}% complété</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-500"
              style={{ width: `${(currentStep / 5) * 100}%` }}
            />
          </div>
        </div>

        {/* Content Card */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          {renderStep()}

          {/* Navigation Buttons */}
          <div className="flex justify-between mt-8">
            {currentStep > 1 && (
              <button
                onClick={handleBack}
                className="flex items-center px-6 py-3 text-gray-600 hover:text-gray-800 transition-colors"
              >
                <ArrowLeft className="h-5 w-5 mr-2" />
                Retour
              </button>
            )}
            
            <button
              onClick={handleNext}
              disabled={loading}
              className={`flex items-center px-8 py-3 bg-blue-600 text-white rounded-lg 
                         font-semibold hover:bg-blue-700 transition-all ml-auto
                         ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              {loading ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" />
              ) : (
                <>
                  {currentStep === 5 ? 'Terminer' : 'Continuer'}
                  <ArrowRight className="h-5 w-5 ml-2" />
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Step 1: Welcome
const StepWelcome = () => (
  <div className="text-center">
    <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
      <Plane className="h-10 w-10 text-blue-600" />
    </div>
    
    <h2 className="text-3xl font-bold mb-4">Bienvenue sur GlobeGenius ! 🎉</h2>
    <p className="text-gray-600 mb-6">
      Personnalisons votre expérience en quelques étapes simples pour vous envoyer 
      les meilleures offres de voyage.
    </p>
    
    <div className="bg-blue-50 rounded-lg p-6 text-left">
      <h3 className="font-semibold mb-3 flex items-center">
        <Sparkles className="h-5 w-5 text-blue-600 mr-2" />
        Ce que vous allez obtenir :
      </h3>
      <ul className="space-y-2">
        <li className="flex items-start">
          <CheckCircle className="h-5 w-5 text-green-500 mr-2 mt-0.5" />
          <span>Alertes personnalisées sur vos destinations favorites</span>
        </li>
        <li className="flex items-start">
          <CheckCircle className="h-5 w-5 text-green-500 mr-2 mt-0.5" />
          <span>Détection automatique des prix cassés jusqu'à -80%</span>
        </li>
        <li className="flex items-start">
          <CheckCircle className="h-5 w-5 text-green-500 mr-2 mt-0.5" />
          <span>Notifications instantanées des erreurs de prix</span>
        </li>
      </ul>
    </div>
  </div>
);

// Step 2: Profile & Home Airports
const StepProfile = ({ formData, setFormData, popularAirports }) => (
  <div>
    <h2 className="text-2xl font-bold mb-6">Faisons connaissance ! 👋</h2>
    
    <div className="mb-6">
      <label className="block text-sm font-medium text-gray-700 mb-2">
        Comment dois-je vous appeler ?
      </label>
      <input
        type="text"
        value={formData.firstName}
        onChange={(e) => setFormData({ ...formData, firstName: e.target.value })}
        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        placeholder="Votre prénom"
      />
    </div>
    
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        <MapPin className="inline h-4 w-4 mr-1" />
        D'où partez-vous habituellement ?
      </label>
      <p className="text-sm text-gray-500 mb-3">
        Sélectionnez vos aéroports de départ préférés
      </p>
      
      <div className="grid grid-cols-2 gap-3">
        {popularAirports.map((airport) => (
          <label
            key={airport.code}
            className={`flex items-center p-3 border rounded-lg cursor-pointer transition-all
                       ${formData.homeAirports.includes(airport.code)
                         ? 'border-blue-500 bg-blue-50'
                         : 'border-gray-300 hover:border-gray-400'}`}
          >
            <input
              type="checkbox"
              checked={formData.homeAirports.includes(airport.code)}
              onChange={(e) => {
                if (e.target.checked) {
                  setFormData({
                    ...formData,
                    homeAirports: [...formData.homeAirports, airport.code]
                  });
                } else {
                  setFormData({
                    ...formData,
                    homeAirports: formData.homeAirports.filter(code => code !== airport.code)
                  });
                }
              }}
              className="sr-only"
            />
            <div className="flex-1">
              <span className="font-medium">{airport.code}</span>
              <span className="text-sm text-gray-500 ml-2">{airport.city}</span>
            </div>
            {formData.homeAirports.includes(airport.code) && (
              <CheckCircle className="h-5 w-5 text-blue-600" />
            )}
          </label>
        ))}
      </div>
    </div>
  </div>
);

// Step 3: Travel Types
const StepTravelTypes = ({ formData, setFormData }) => {
  const travelTypes = [
    { id: 'leisure', label: 'Loisirs / Vacances', emoji: '🏖️', description: 'Détente et découverte' },
    { id: 'business', label: 'Voyages d\'affaires', emoji: '💼', description: 'Déplacements professionnels' },
    { id: 'family', label: 'Voyages en famille', emoji: '👨‍👩‍👧‍👦', description: 'Avec enfants' },
    { id: 'adventure', label: 'Aventure', emoji: '🎒', description: 'Exploration et sensations' },
    { id: 'romantic', label: 'Romantique', emoji: '💑', description: 'En couple' },
    { id: 'solo', label: 'Solo', emoji: '🚶', description: 'Voyageur indépendant' }
  ];

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Quel type de voyageur êtes-vous ? ✈️</h2>
      <p className="text-gray-600 mb-6">
        Sélectionnez tous les types de voyages qui vous intéressent
      </p>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {travelTypes.map((type) => (
          <label
            key={type.id}
            className={`flex items-start p-4 border-2 rounded-xl cursor-pointer transition-all
                       ${formData.travelTypes.includes(type.id)
                         ? 'border-blue-500 bg-blue-50'
                         : 'border-gray-200 hover:border-gray-300'}`}
          >
            <input
              type="checkbox"
              checked={formData.travelTypes.includes(type.id)}
              onChange={(e) => {
                if (e.target.checked) {
                  setFormData({
                    ...formData,
                    travelTypes: [...formData.travelTypes, type.id]
                  });
                } else {
                  setFormData({
                    ...formData,
                    travelTypes: formData.travelTypes.filter(id => id !== type.id)
                  });
                }
              }}
              className="sr-only"
            />
            <span className="text-2xl mr-3">{type.emoji}</span>
            <div className="flex-1">
              <span className="font-medium block">{type.label}</span>
              <span className="text-sm text-gray-500">{type.description}</span>
            </div>
            {formData.travelTypes.includes(type.id) && (
              <CheckCircle className="h-5 w-5 text-blue-600 mt-0.5" />
            )}
          </label>
        ))}
      </div>
    </div>
  );
};

// Step 4: Favorite Destinations
const StepDestinations = ({ formData, setFormData, popularDestinations }) => (
  <div>
    <h2 className="text-2xl font-bold mb-6">Vos destinations de rêve ? 🌍</h2>
    <p className="text-gray-600 mb-6">
      Sélectionnez les destinations qui vous font rêver pour recevoir les meilleures offres
    </p>
    
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {popularDestinations.map((dest) => (
        <label
          key={dest.code}
          className={`flex flex-col items-center p-4 border-2 rounded-xl cursor-pointer transition-all
                     ${formData.favoriteDestinations.includes(dest.code)
                       ? 'border-blue-500 bg-blue-50'
                       : 'border-gray-200 hover:border-gray-300'}`}
        >
          <input
            type="checkbox"
            checked={formData.favoriteDestinations.includes(dest.code)}
            onChange={(e) => {
              if (e.target.checked) {
                setFormData({
                  ...formData,
                  favoriteDestinations: [...formData.favoriteDestinations, dest.code]
                });
              } else {
                setFormData({
                  ...formData,
                  favoriteDestinations: formData.favoriteDestinations.filter(code => code !== dest.code)
                });
              }
            }}
            className="sr-only"
          />
          <span className="text-3xl mb-2">{dest.emoji}</span>
          <span className="font-medium text-sm text-center">{dest.name}</span>
          {formData.favoriteDestinations.includes(dest.code) && (
            <CheckCircle className="h-4 w-4 text-blue-600 mt-1" />
          )}
        </label>
      ))}
    </div>
    
    <div className="mt-6 p-4 bg-yellow-50 rounded-lg">
      <p className="text-sm text-yellow-800">
        💡 Astuce : Plus vous sélectionnez de destinations, plus vous recevrez d'opportunités !
      </p>
    </div>
  </div>
);

// Step 5: Notification Preferences
const StepNotifications = ({ formData, setFormData }) => (
  <div>
    <h2 className="text-2xl font-bold mb-6">Comment souhaitez-vous être alerté ? 🔔</h2>
    
    <div className="space-y-4">
      <label className={`flex items-start p-4 border-2 rounded-xl cursor-pointer transition-all
                       ${formData.alertFrequency === 'instant'
                         ? 'border-blue-500 bg-blue-50'
                         : 'border-gray-200 hover:border-gray-300'}`}>
        <input
          type="radio"
          name="frequency"
          value="instant"
          checked={formData.alertFrequency === 'instant'}
          onChange={(e) => setFormData({ ...formData, alertFrequency: e.target.value })}
          className="sr-only"
        />
        <div className="flex-1">
          <div className="flex items-center mb-1">
            <TrendingDown className="h-5 w-5 text-blue-600 mr-2" />
            <span className="font-semibold">Alertes instantanées</span>
            <span className="ml-2 px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">
              Recommandé
            </span>
          </div>
          <p className="text-sm text-gray-600">
            Recevez une notification dès qu'une offre exceptionnelle est détectée
          </p>
        </div>
        {formData.alertFrequency === 'instant' && (
          <CheckCircle className="h-5 w-5 text-blue-600 mt-0.5" />
        )}
      </label>
      
      <label className={`flex items-start p-4 border-2 rounded-xl cursor-pointer transition-all
                       ${formData.alertFrequency === 'daily'
                         ? 'border-blue-500 bg-blue-50'
                         : 'border-gray-200 hover:border-gray-300'}`}>
        <input
          type="radio"
          name="frequency"
          value="daily"
          checked={formData.alertFrequency === 'daily'}
          onChange={(e) => setFormData({ ...formData, alertFrequency: e.target.value })}
          className="sr-only"
        />
        <div className="flex-1">
          <div className="flex items-center mb-1">
            <Mail className="h-5 w-5 text-gray-600 mr-2" />
            <span className="font-semibold">Résumé quotidien</span>
          </div>
          <p className="text-sm text-gray-600">
            Un email récapitulatif chaque matin avec les meilleures offres
          </p>
        </div>
        {formData.alertFrequency === 'daily' && (
          <CheckCircle className="h-5 w-5 text-blue-600 mt-0.5" />
        )}
      </label>
      
      <label className={`flex items-start p-4 border-2 rounded-xl cursor-pointer transition-all
                       ${formData.alertFrequency === 'weekly'
                         ? 'border-blue-500 bg-blue-50'
                         : 'border-gray-200 hover:border-gray-300'}`}>
        <input
          type="radio"
          name="frequency"
          value="weekly"
          checked={formData.alertFrequency === 'weekly'}
          onChange={(e) => setFormData({ ...formData, alertFrequency: e.target.value })}
          className="sr-only"
        />
        <div className="flex-1">
          <div className="flex items-center mb-1">
            <Globe className="h-5 w-5 text-gray-600 mr-2" />
            <span className="font-semibold">Hebdomadaire</span>
          </div>
          <p className="text-sm text-gray-600">
            Les meilleures offres de la semaine, tous les lundis
          </p>
        </div>
        {formData.alertFrequency === 'weekly' && (
          <CheckCircle className="h-5 w-5 text-blue-600 mt-0.5" />
        )}
      </label>
    </div>
    
    <div className="mt-6 p-4 bg-green-50 rounded-lg">
      <p className="text-sm text-green-800">
        ✅ Vous pourrez modifier vos préférences à tout moment depuis votre profil
      </p>
    </div>
  </div>
);

export default Onboarding;