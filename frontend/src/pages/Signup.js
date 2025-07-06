// frontend/src/pages/Signup.js

import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { motion } from 'framer-motion';
import { Plane, Mail, Lock, MapPin, Loader, Navigation } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';

// Aéroports populaires en France et Europe
const POPULAR_AIRPORTS = [
  { code: 'CDG', name: 'Paris Charles de Gaulle', city: 'Paris', country: 'FR' },
  { code: 'ORY', name: 'Paris Orly', city: 'Paris', country: 'FR' },
  { code: 'NCE', name: 'Nice Côte d\'Azur', city: 'Nice', country: 'FR' },
  { code: 'LYS', name: 'Lyon Saint-Exupéry', city: 'Lyon', country: 'FR' },
  { code: 'MRS', name: 'Marseille Provence', city: 'Marseille', country: 'FR' },
  { code: 'TLS', name: 'Toulouse Blagnac', city: 'Toulouse', country: 'FR' },
  { code: 'BOD', name: 'Bordeaux', city: 'Bordeaux', country: 'FR' },
  { code: 'NTE', name: 'Nantes Atlantique', city: 'Nantes', country: 'FR' },
  { code: 'LHR', name: 'London Heathrow', city: 'Londres', country: 'GB' },
  { code: 'AMS', name: 'Amsterdam Schiphol', city: 'Amsterdam', country: 'NL' },
  { code: 'BCN', name: 'Barcelona El Prat', city: 'Barcelone', country: 'ES' },
  { code: 'MAD', name: 'Madrid Barajas', city: 'Madrid', country: 'ES' },
  { code: 'FCO', name: 'Rome Fiumicino', city: 'Rome', country: 'IT' },
  { code: 'BRU', name: 'Brussels', city: 'Bruxelles', country: 'BE' },
];

const Signup = () => {
  const navigate = useNavigate();
  const { signup } = useAuth();
  const [loading, setLoading] = useState(false);
  const [detectingLocation, setDetectingLocation] = useState(false);
  const [selectedAirport, setSelectedAirport] = useState('');
  const [showAirportList, setShowAirportList] = useState(false);
  const [airportSearch, setAirportSearch] = useState('');
  
  const { register, handleSubmit, formState: { errors } } = useForm();

  // Tenter la géolocalisation au chargement
  useEffect(() => {
    detectNearestAirport();
  }, []);

  const detectNearestAirport = async () => {
    setDetectingLocation(true);
    
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          try {
            // Dans un vrai cas, on appellerait une API pour trouver l'aéroport le plus proche
            // Pour la démo, on simule avec Paris CDG
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Logique simplifiée : si en France, suggérer CDG
            setSelectedAirport('CDG');
            setAirportSearch('Paris Charles de Gaulle (CDG)');
            toast.success('Aéroport détecté : Paris CDG');
          } catch (error) {
            console.error('Erreur détection aéroport:', error);
          } finally {
            setDetectingLocation(false);
          }
        },
        (error) => {
          console.error('Erreur géolocalisation:', error);
          setDetectingLocation(false);
        }
      );
    } else {
      setDetectingLocation(false);
    }
  };

  const filteredAirports = POPULAR_AIRPORTS.filter(airport => 
    airport.name.toLowerCase().includes(airportSearch.toLowerCase()) ||
    airport.city.toLowerCase().includes(airportSearch.toLowerCase()) ||
    airport.code.toLowerCase().includes(airportSearch.toLowerCase())
  );

  const onSubmit = async (data) => {
    if (!selectedAirport) {
      toast.error('Veuillez sélectionner un aéroport de départ');
      return;
    }

    setLoading(true);
    
    try {
      const signupData = {
        email: data.email,
        password: data.password,
        home_airports: [selectedAirport] // On envoie directement l'aéroport
      };
      
      const result = await signup(signupData);
      if (result.success) {
        toast.success('Compte créé avec succès !');
        // Pas d'onboarding complexe, on va direct au dashboard
        navigate('/dashboard');
      }
    } catch (error) {
      console.error('Signup error:', error);
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
            <Plane className="h-8 w-8 text-blue-600" />
            <span className="text-2xl font-bold">GlobeGenius</span>
          </Link>
          
          <h2 className="text-3xl font-bold text-gray-900">
            Commencez à économiser
          </h2>
          <p className="text-gray-600 mt-2">
            Créez votre compte en 30 secondes
          </p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Email */}
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
                         focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="vous@exemple.com"
              />
            </div>
            {errors.email && (
              <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
            )}
          </div>

          {/* Mot de passe */}
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
                         focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="••••••••"
              />
            </div>
            {errors.password && (
              <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
            )}
          </div>

          {/* Aéroport de départ */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Votre aéroport de départ principal
            </label>
            <div className="relative">
              <MapPin className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
              <input
                type="text"
                value={airportSearch}
                onChange={(e) => {
                  setAirportSearch(e.target.value);
                  setShowAirportList(true);
                }}
                onFocus={() => setShowAirportList(true)}
                className="w-full pl-10 pr-10 py-3 border border-gray-300 rounded-lg 
                         focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Ex: Paris, CDG..."
              />
              {detectingLocation && (
                <Loader className="absolute right-3 top-3 h-5 w-5 text-blue-600 animate-spin" />
              )}
              {!detectingLocation && (
                <button
                  type="button"
                  onClick={detectNearestAirport}
                  className="absolute right-3 top-3 text-blue-600 hover:text-blue-700"
                  title="Détecter ma position"
                >
                  <Navigation className="h-5 w-5" />
                </button>
              )}
            </div>
            
            {/* Liste déroulante des aéroports */}
            {showAirportList && airportSearch && (
              <div className="absolute z-10 mt-1 w-full bg-white rounded-lg shadow-lg border border-gray-200 max-h-60 overflow-y-auto">
                {filteredAirports.map(airport => (
                  <button
                    key={airport.code}
                    type="button"
                    onClick={() => {
                      setSelectedAirport(airport.code);
                      setAirportSearch(`${airport.city} (${airport.code})`);
                      setShowAirportList(false);
                    }}
                    className="w-full px-4 py-3 text-left hover:bg-gray-50 flex items-center justify-between"
                  >
                    <div>
                      <div className="font-semibold">{airport.city}</div>
                      <div className="text-sm text-gray-600">{airport.name}</div>
                    </div>
                    <span className="text-lg font-bold text-gray-500">{airport.code}</span>
                  </button>
                ))}
              </div>
            )}
            
            {selectedAirport && (
              <p className="mt-2 text-sm text-green-600 flex items-center">
                ✓ Vous recevrez les meilleures offres au départ de {selectedAirport}
              </p>
            )}
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={loading || !selectedAirport}
            className="w-full py-3 bg-blue-600 text-white rounded-lg font-semibold 
                     hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed
                     transition-all duration-200 transform hover:scale-[1.02]"
          >
            {loading ? (
              <div className="flex items-center justify-center">
                <Loader className="animate-spin h-5 w-5 mr-2" />
                Création en cours...
              </div>
            ) : (
              'Créer mon compte et recevoir les alertes'
            )}
          </button>
        </form>

        {/* Info supplémentaire */}
        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <p className="text-sm text-blue-800 text-center">
            💡 Vous pourrez personnaliser vos destinations favorites et préférences 
            plus tard, après avoir reçu vos premières alertes.
          </p>
        </div>

        <div className="mt-6 text-center">
          <p className="text-gray-600">
            Déjà un compte ?{' '}
            <Link to="/login" className="text-blue-600 font-semibold hover:underline">
              Connectez-vous
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
};

export default Signup;