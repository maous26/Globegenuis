import React, { useState, useEffect } from 'react';

const ConnectionTest = () => {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const addResult = (message, type = 'info') => {
    setResults(prev => [...prev, { message, type, timestamp: new Date().toLocaleTimeString() }]);
    console.log(`[${type.toUpperCase()}] ${message}`);
  };

  const testConnection = async () => {
    setLoading(true);
    setResults([]);
    
    const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    const API_BASE_URL = `${API_URL}/api/v1`;
    
    addResult(`🔧 Configuration API: ${API_BASE_URL}`, 'info');
    
    // Test 1: Backend accessibility
    try {
      const response = await fetch(`${API_URL}/docs`);
      if (response.ok) {
        addResult('✅ Backend accessible (documentation)', 'success');
      } else {
        addResult(`❌ Backend inaccessible: ${response.status}`, 'error');
      }
    } catch (error) {
      addResult(`❌ Erreur connexion backend: ${error.message}`, 'error');
    }
    
    // Test 2: Login endpoint
    try {
      const formData = new FormData();
      formData.append('username', 'admin@globegenius.com');
      formData.append('password', 'admin123');

      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        addResult('✅ Login direct réussi!', 'success');
        addResult(`Token: ${data.access_token.substring(0, 50)}...`, 'success');
      } else {
        const error = await response.text();
        addResult(`❌ Login échoué: ${response.status} - ${error}`, 'error');
      }
    } catch (error) {
      addResult(`❌ Erreur login: ${error.message}`, 'error');
    }
    
    // Test 3: Test with axios (same as the app)
    try {
      const axios = (await import('axios')).default;
      const api = axios.create({
        baseURL: API_BASE_URL,
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const response = await api.post('/auth/login', new URLSearchParams({
        username: 'admin@globegenius.com',
        password: 'admin123',
      }), {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });

      addResult('✅ Login avec axios réussi!', 'success');
      addResult(`Token axios: ${response.data.access_token.substring(0, 50)}...`, 'success');
    } catch (error) {
      addResult(`❌ Erreur axios: ${error.message}`, 'error');
      if (error.response) {
        addResult(`Status: ${error.response.status}`, 'error');
        addResult(`Data: ${JSON.stringify(error.response.data)}`, 'error');
      } else if (error.request) {
        addResult('❌ Pas de réponse du serveur (axios)', 'error');
      }
    }
    
    setLoading(false);
  };

  useEffect(() => {
    testConnection();
  }, []);

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h2>🔍 Test de Connexion</h2>
      
      <button 
        onClick={testConnection} 
        disabled={loading}
        style={{
          padding: '10px 20px',
          backgroundColor: loading ? '#ccc' : '#007bff',
          color: 'white',
          border: 'none',
          borderRadius: '5px',
          cursor: loading ? 'not-allowed' : 'pointer',
          marginBottom: '20px'
        }}
      >
        {loading ? 'Test en cours...' : 'Relancer le test'}
      </button>

      <div>
        {results.map((result, index) => (
          <div
            key={index}
            style={{
              padding: '10px',
              margin: '5px 0',
              borderRadius: '5px',
              backgroundColor: 
                result.type === 'success' ? '#d4edda' :
                result.type === 'error' ? '#f8d7da' :
                '#d1ecf1',
              color:
                result.type === 'success' ? '#155724' :
                result.type === 'error' ? '#721c24' :
                '#0c5460'
            }}
          >
            <strong>{result.timestamp}</strong> - {result.message}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ConnectionTest;
