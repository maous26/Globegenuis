const axios = require('axios');

const API_URL = 'http://localhost:8000/api/v1';

async function testSignup() {
  try {
    console.log('Testing signup API...');
    
    // 1. Test OPTIONS request
    console.log('Step 1: Testing OPTIONS request to /users/signup');
    try {
      const optionsResponse = await axios({
        method: 'OPTIONS',
        url: `${API_URL}/users/signup`,
        headers: {
          'Origin': 'http://localhost:3004',
          'Access-Control-Request-Method': 'POST',
          'Access-Control-Request-Headers': 'Content-Type,Authorization'
        }
      });
      console.log('OPTIONS response:', {
        status: optionsResponse.status,
        headers: optionsResponse.headers,
      });
    } catch (error) {
      console.error('OPTIONS request failed:', {
        status: error.response?.status,
        statusText: error.response?.statusText,
        headers: error.response?.headers,
        data: error.response?.data
      });
    }
    
    // 2. Test signup with a random user
    const testEmail = `test${Date.now()}@example.com`;
    const testPassword = 'password123';
    const testUser = {
      email: testEmail,
      password: testPassword,
      first_name: 'Test',
      last_name: 'User'
    };
    
    console.log('Step 2: Testing signup with user:', testUser);
    let userData;
    try {
      const signupResponse = await axios.post(
        `${API_URL}/users/signup`,
        testUser,
        {
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Origin': 'http://localhost:3004'
          }
        }
      );
      
      console.log('Signup successful:', {
        status: signupResponse.status,
        data: signupResponse.data
      });
      
      userData = signupResponse.data;
      
      // 3. Test login with the created user
      console.log('Step 3: Testing login with created user');
      const loginParams = new URLSearchParams();
      loginParams.append('username', testEmail);
      loginParams.append('password', testPassword);
      
      try {
        const loginResponse = await axios.post(
          `${API_URL}/auth/login`,
          loginParams,
          {
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
              'Accept': 'application/json',
              'Origin': 'http://localhost:3004'
            }
          }
        );
        
        console.log('Login successful:', {
          status: loginResponse.status,
          data: loginResponse.data
        });
        
        // 4. Test getting user profile with token
        if (loginResponse.data.access_token) {
          console.log('Step 4: Testing user profile fetch with token');
          try {
            const profileResponse = await axios.get(
              `${API_URL}/users/me`,
              {
                headers: {
                  'Authorization': `Bearer ${loginResponse.data.access_token}`,
                  'Accept': 'application/json',
                  'Origin': 'http://localhost:3004'
                }
              }
            );
            
            console.log('Profile fetch successful:', {
              status: profileResponse.status,
              data: profileResponse.data
            });
          } catch (error) {
            console.error('Profile fetch failed:', {
              status: error.response?.status,
              statusText: error.response?.statusText,
              data: error.response?.data
            });
          }
        }
      } catch (error) {
        console.error('Login failed:', {
          status: error.response?.status,
          statusText: error.response?.statusText,
          data: error.response?.data
        });
      }
    } catch (error) {
      console.error('Signup failed:', {
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data
      });
    }
  } catch (error) {
    console.error('Test failed with error:', error.message);
  }
}

// Run the test
testSignup();

// Export for reuse
module.exports = { testSignup };
