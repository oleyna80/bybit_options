import React from 'react';

interface ExpiryFilterProps {
  options: string[];
  selected: string;
  onChange: (value: string) => void;
}

export const ExpiryFilter: React.FC<ExpiryFilterProps> = ({
  options,
  selected,
  onChange,
}) => {
  return (
    <div className="flex flex-wrap gap-1">
      {options.map(option => (
        <button
          key={option}
          onClick={() => onChange(option)}
          className={`chip ${selected === option ? 'chip-default' : 'chip-outline'}`}
        >
          {option}
        </button>
      ))}
    </div>
  );
};