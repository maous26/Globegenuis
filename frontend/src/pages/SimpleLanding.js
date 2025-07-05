import React from 'react';
import { Link } from 'react-router-dom';

const SimpleLanding = () => {
  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-md p-8">
        <h1 className="text-3xl font-bold mb-4 text-gray-900">Bienvenue sur GlobeGenius</h1>
        <p className="text-gray-700 mb-6">
          L'IA qui détecte les erreurs de prix voyage automatiquement
        </p>
        
        <div className="flex gap-4">
          <Link to="/login" className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
            Connexion
          </Link>
          <Link to="/signup" className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300">
            Inscription
          </Link>
          <Link to="/test" className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700">
            Test Component
          </Link>
        </div>
      </div>
    </div>
  );
};

export default SimpleLanding;
