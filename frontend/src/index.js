import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

// Add debug logging
console.log('Starting application...');
console.log('DOM root element exists:', !!document.getElementById('root'));

const root = ReactDOM.createRoot(document.getElementById('root'));
console.log('Created ReactDOM root');

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
console.log('Rendered App component');