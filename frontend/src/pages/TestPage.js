import React from 'react';
import ConnectionTest from '../components/ConnectionTest';

const TestPage = () => {
  return (
    <div style={{ padding: '20px' }}>
      <h1>🔍 Page de Test de Connexion</h1>
      <p>Cette page teste la connexion entre le frontend et le backend.</p>
      <ConnectionTest />
    </div>
  );
};

export default TestPage;
