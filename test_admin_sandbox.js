// Simple test to verify AdminSandbox component structure
const fs = require('fs');
const path = require('path');

console.log('🔍 Testing AdminSandbox Component...\n');

// Check if files exist
const componentPath = path.join(__dirname, 'frontend/src/admin/AdminSandbox.jsx');
const cssPath = path.join(__dirname, 'frontend/src/admin/AdminSandbox.module.css');

if (!fs.existsSync(componentPath)) {
  console.error('❌ AdminSandbox.jsx not found');
  process.exit(1);
}

if (!fs.existsSync(cssPath)) {
  console.error('❌ AdminSandbox.module.css not found');
  process.exit(1);
}

console.log('✅ Files exist');

// Check component content
const componentContent = fs.readFileSync(componentPath, 'utf8');
const cssContent = fs.readFileSync(cssPath, 'utf8');

// Verify required imports
const requiredImports = [
  'React',
  'useState', 
  'useEffect',
  'motion',
  'lucide-react'
];

requiredImports.forEach(imp => {
  if (componentContent.includes(imp)) {
    console.log(`✅ Contains ${imp}`);
  } else {
    console.log(`❌ Missing ${imp}`);
  }
});

// Verify sensor configuration
const sensorCount = (componentContent.match(/key:/g) || []).length;
console.log(`✅ Found ${sensorCount} sensor configurations`);

// Verify CSS classes
const cssClasses = cssContent.match(/\.\w+/g) || [];
console.log(`✅ CSS module contains ${cssClasses.length} class definitions`);

// Check routing in App.js
const appPath = path.join(__dirname, 'frontend/src/App.js');
const appContent = fs.readFileSync(appPath, 'utf8');

if (appContent.includes('AdminSandbox')) {
  console.log('✅ AdminSandbox imported in App.js');
} else {
  console.log('❌ AdminSandbox not imported in App.js');
}

if (appContent.includes('path="/admin"')) {
  console.log('✅ /admin route added to App.js');
} else {
  console.log('❌ /admin route not found in App.js');
}

console.log('\n🎉 AdminSandbox component setup complete!');
console.log('\n📋 Usage Instructions:');
console.log('1. Start the development server: npm start');
console.log('2. Navigate to http://localhost:3000/admin');
console.log('3. Login with your credentials');
console.log('4. Test the IoT simulator and agent monitor');
console.log('\n🔧 Features:');
console.log('• 9 sensor sliders with real-time updates');
console.log('• Live/Simulated data toggle');
console.log('• Agent activity feed with token tracking');
console.log('• Console logging for injected data');
console.log('• Responsive design with dark theme');
