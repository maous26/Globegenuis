// Frontend React component to test API KPIs
import React, { useState, useEffect } from 'react';
import AdminApiService from '../services/adminApi';

const ApiKpisTest = () => {
  const [apiKpisData, setApiKpisData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const loadApiKpis = async () => {
      try {
        setLoading(true);
        setError(null);
        
        console.log('Loading API KPIs data...');
        const data = await AdminApiService.getApiKpis('24h');
        console.log('API KPIs data loaded:', data);
        
        setApiKpisData(data);
      } catch (err) {
        console.error('Error loading API KPIs:', err);
        setError(err.message || 'Failed to load API KPIs');
      } finally {
        setLoading(false);
      }
    };
    
    loadApiKpis();
  }, []);
  
  if (loading) {
    return <div>Loading API KPIs data...</div>;
  }
  
  if (error) {
    return <div style={{ color: 'red' }}>Error: {error}</div>;
  }
  
  if (!apiKpisData) {
    return <div>No API KPIs data available.</div>;
  }
  
  return (
    <div>
      <h2>API KPIs Test</h2>
      <pre>{JSON.stringify(apiKpisData, null, 2)}</pre>
    </div>
  );
};

export default ApiKpisTest;
