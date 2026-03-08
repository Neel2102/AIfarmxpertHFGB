// Quick test script to verify the frontend-backend connection
const testPayload = {
  user_input: "What crops should I plant this season?",
  agent_role: "farmer_coach", 
  user_id: 1
};

console.log('🔌 Testing Frontend-Backend Connection');
console.log('Endpoint:', 'http://localhost:8000/api/agent/process');
console.log('Payload:', JSON.stringify(testPayload, null, 2));

// Test with fetch (same as frontend)
fetch('http://localhost:8000/api/agent/process', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(testPayload)
})
.then(response => {
  console.log('✅ Response status:', response.status);
  return response.json();
})
.then(data => {
  console.log('✅ Response data:', JSON.stringify(data, null, 2));
  
  // Check if response contains expected farm context
  if (data?.response && data?.response.includes('Farm Name:')) {
    console.log('🎯 SUCCESS: Farm context injected into response!');
  } else {
    console.log('⚠️  WARNING: Farm context may not be properly injected');
  }
})
.catch(error => {
  console.error('❌ ERROR:', error.message);
});
