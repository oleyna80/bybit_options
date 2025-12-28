// Simple Node.js test for API integration
const fetch = require('node-fetch');

async function testAPIIntegration() {
    console.log('🧪 Testing API Integration...\n');
    
    try {
        // Test 1: Positions API
        console.log('1. Testing /api/v1/positions...');
        const positionsResponse = await fetch('http://localhost:8000/api/v1/positions');
        const positionsData = await positionsResponse.json();
        console.log(`   ✅ Positions: ${positionsData.count} positions loaded`);
        
        // Test 2: Portfolio API  
        console.log('2. Testing /api/v1/risk/portfolio...');
        const portfolioResponse = await fetch('http://localhost:8000/api/v1/risk/portfolio');
        const portfolioData = await portfolioResponse.json();
        console.log(`   ✅ Portfolio: Vega = $${portfolioData.total_vega_usd.toFixed(2)}`);
        
        // Test 3: Options Board API
        console.log('3. Testing /api/v1/options-board...');
        const optionsResponse = await fetch('http://localhost:8000/api/v1/options-board?base_coin=BTC');
        const optionsData = await optionsResponse.json();
        console.log(`   ✅ Options: ${optionsData.options.length} options available`);
        
        // Test 4: Coins API
        console.log('4. Testing /api/v1/coins...');
        const coinsResponse = await fetch('http://localhost:8000/api/v1/coins');
        const coinsData = await coinsResponse.json();
        console.log(`   ✅ Coins: ${coinsData.length} coins supported`);
        
        console.log('\n🎉 All API endpoints working correctly!');
        console.log('\nIntegration Summary:');
        console.log(`- Positions: ${positionsData.count} active positions`);
        console.log(`- Portfolio Risk: Vega = $${portfolioData.total_vega_usd.toFixed(2)}, Theta = $${portfolioData.total_theta_usd.toFixed(2)}/day`);
        console.log(`- Options Board: ${optionsData.options.length} options for BTC`);
        console.log(`- Supported Coins: ${coinsData.join(', ')}`);
        
        return true;
    } catch (error) {
        console.error('\n❌ API Integration Test Failed:', error.message);
        return false;
    }
}

// Run test if executed directly
if (require.main === module) {
    testAPIIntegration().then(success => {
        process.exit(success ? 0 : 1);
    });
}

