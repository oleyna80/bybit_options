import React from 'react';

interface CoinSelectorProps {
  coins: string[];
  selected: string;
  onChange: (coin: string) => void;
  isLoading?: boolean;
}

export const CoinSelector: React.FC<CoinSelectorProps> = ({
  coins,
  selected,
  onChange,
  isLoading = false,
}) => {
  return (
    <div className="flex flex-wrap gap-2">
      {isLoading ? (
        <div className="text-sm text-muted-foreground">Loading coins...</div>
      ) : (
        coins.map(coin => (
          <button
            key={coin}
            onClick={() => onChange(coin)}
            className={`
              px-4 py-2 rounded-md font-semibold text-sm
              transition-all duration-200
              ${
                selected === coin
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/50'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600 hover:text-white'
              }
            `}
          >
            {coin}
          </button>
        ))
      )}
    </div>
  );
};
