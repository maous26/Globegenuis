import { authAPI } from '../services/api';

const TestLoginComponent = () => {
  const handleTestLogin = async () => {
    console.log('🔧 Starting test login...');
    
    try {
      console.log('🔐 Calling authAPI.login...');
      const response = await authAPI.login('admin@globegenius.com', 'admin123');
      console.log('✅ Login successful:', response.data);
      alert('Login successful!');
    } catch (error) {
      console.error('❌ Login failed:', error);
      console.error('Error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
        hasResponse: !!error.response,
        hasRequest: !!error.request
      });
      alert(`Login failed: ${error.message}`);
    }
  };

  return (
    <div style={{ position: 'fixed', top: '10px', right: '10px', zIndex: 9999 }}>
      <button 
        onClick={handleTestLogin}
        style={{
          padding: '10px 20px',
          backgroundColor: '#dc3545',
          color: 'white',
          border: 'none',
          borderRadius: '5px',
          cursor: 'pointer'
        }}
      >
        🧪 Test Login Direct
      </button>
    </div>
  );
};

export default TestLoginComponent;
