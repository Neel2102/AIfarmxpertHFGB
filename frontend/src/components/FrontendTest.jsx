import React, { useState } from 'react';
import farmxpertAPI from '../services/farmxpertAPI';

const FrontendTest = () => {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);

  const testConnection = async () => {
    setLoading(true);
    setResponse('');
    
    try {
      const result = await farmxpertAPI.sendMessage(
        message || 'Hello, what crops should I plant?',
        'farmer_coach',
        {
          farm_location: 'ahmedabad, India',
          farm_size: '5 acres',
          user_id: 1
        }
      );
      
      setResponse(JSON.stringify(result, null, 2));
    } catch (error) {
      setResponse(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h2>🔌 Frontend-Backend Connection Test</h2>
      
      <div style={{ marginBottom: '20px' }}>
        <label>
          Test Message: 
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Enter a test message..."
            style={{ width: '300px', marginLeft: '10px', padding: '5px' }}
          />
        </label>
      </div>
      
      <button 
        onClick={testConnection}
        disabled={loading}
        style={{
          padding: '10px 20px',
          backgroundColor: loading ? '#ccc' : '#007bff',
          color: 'white',
          border: 'none',
          borderRadius: '5px',
          cursor: loading ? 'not-allowed' : 'pointer'
        }}
      >
        {loading ? 'Testing...' : 'Test Connection'}
      </button>
      
      {response && (
        <div style={{ marginTop: '20px' }}>
          <h3>Response:</h3>
          <pre style={{ 
            backgroundColor: '#f5f5f5', 
            padding: '15px', 
            borderRadius: '5px',
            overflow: 'auto',
            maxHeight: '400px'
          }}>
            {response}
          </pre>
        </div>
      )}
      
      <div style={{ marginTop: '30px', padding: '15px', backgroundColor: '#e7f3ff', borderRadius: '5px' }}>
        <h4>📋 Test Details:</h4>
        <ul>
          <li><strong>Endpoint:</strong> POST /api/agent/process</li>
          <li><strong>Backend URL:</strong> {process.env.REACT_APP_API_URL || '/api'}</li>
          <li><strong>Agent Role:</strong> farmer_coach</li>
          <li><strong>User ID:</strong> 1</li>
          <li><strong>Expected:</strong> JSON response with farm context injected</li>
        </ul>
      </div>
    </div>
  );
};

export default FrontendTest;
