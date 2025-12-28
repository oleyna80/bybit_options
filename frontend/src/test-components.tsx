import PriceChart from './components/Charts/PriceChart';
import { IVRankChart } from './components/Charts/IVRankChart';
import HistoricalDataPage from './components/HistoricalDataPage';
import './index.css';

const TestApp = () => {
  return (
    <div className="min-h-screen bg-gray-900 p-6">
      <h1 className="text-2xl font-bold text-white mb-6">Test Components</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-gray-800 rounded-lg p-4">
          <h2 className="text-xl font-semibold text-white mb-4">PriceChart Component</h2>
          <div className="h-64">
            <PriceChart symbol="BTC-PERPETUAL" days={30} height={200} />
          </div>
        </div>
        
        <div className="bg-gray-800 rounded-lg p-4">
          <h2 className="text-xl font-semibold text-white mb-4">IVRankChart Component</h2>
          <div className="h-64">
            <IVRankChart baseCoin="BTC" days={30} height="200px" />
          </div>
        </div>
      </div>
      
      <div className="bg-gray-800 rounded-lg p-4">
        <h2 className="text-xl font-semibold text-white mb-4">HistoricalDataPage Component</h2>
        <div className="h-96 overflow-auto">
          <HistoricalDataPage />
        </div>
      </div>
    </div>
  );
};

// This is just for testing - not meant to be run directly
export default TestApp;