import React from 'react';

const SimpleLoginTest = () => {
  const testSimpleLogin = async () => {
    console.log('🔧 Starting simple login test without interceptors...');
    
    try {
      const API_BASE_URL = 'http://localhost:8000/api/v1';
      
      // Test avec fetch simple (pas d'axios, pas d'intercepteurs)
      const formData = new FormData();
      formData.append('username', 'admin@globegenius.com');
      formData.append('password', 'admin123');

      console.log('📤 Sending request to:', `${API_BASE_URL}/auth/login`);
      
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        body: formData
      });

      console.log('📥 Response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('✅ Simple login SUCCESS!', data);
        alert('Simple login SUCCESS!');
      } else {
        const errorText = await response.text();
        console.error('❌ Simple login FAILED:', response.status, errorText);
        alert(`Simple login FAILED: ${response.status} - ${errorText}`);
      }
    } catch (error) {
      console.error('❌ Simple login ERROR:', error);
      alert(`Simple login ERROR: ${error.message}`);
    }
  };

  const testAxiosLogin = async () => {
    console.log('🔧 Starting axios login test...');
    
    try {
      // Import axios dynamiquement
      const axios = (await import('axios')).default;
      
      const API_BASE_URL = 'http://localhost:8000/api/v1';
      
      // Test avec axios sans intercepteurs
      const response = await axios.post(`${API_BASE_URL}/auth/login`, 
        new URLSearchParams({
          username: 'admin@globegenius.com',
          password: 'admin123',
        }), 
        {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        }
      );

      console.log('✅ Axios login SUCCESS!', response.data);
      alert('Axios login SUCCESS!');
    } catch (error) {
      console.error('❌ Axios login ERROR:', error);
      alert(`Axios login ERROR: ${error.message}`);
    }
  };

  return (
    <div style={{ 
      position: 'fixed', 
      top: '10px', 
      right: '10px', 
      zIndex: 9999, 
      backgroundColor: 'white',
      padding: '10px',
      border: '2px solid red',
      borderRadius: '5px'
    }}>
      <div style={{ marginBottom: '10px', fontWeight: 'bold' }}>
        🧪 Tests de Login Simples
      </div>
      <button 
        onClick={testSimpleLogin}
        style={{
          padding: '5px 10px',
          backgroundColor: '#28a745',
          color: 'white',
          border: 'none',
          borderRadius: '3px',
          cursor: 'pointer',
          margin: '2px',
          display: 'block'
        }}
      >
        Test Fetch Simple
      </button>
      <button 
        onClick={testAxiosLogin}
        style={{
          padding: '5px 10px',
          backgroundColor: '#007bff',
          color: 'white',
          border: 'none',
          borderRadius: '3px',
          cursor: 'pointer',
          margin: '2px',
          display: 'block'
        }}
      >
        Test Axios Simple
      </button>
    </div>
  );
};

export default SimpleLoginTest;
