import React, { useState } from 'react';
import { Download, FileJson, FileText } from 'lucide-react';

interface ExportButtonProps {
  onExport: (format: 'json' | 'md') => void;
}

export const ExportButton: React.FC<ExportButtonProps> = ({ onExport }) => {
  const [isOpen, setIsOpen] = useState(false);

  const handleExport = (format: 'json' | 'md') => {
    onExport(format);
    setIsOpen(false);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="btn btn-outline flex items-center gap-2"
      >
        <Download className="h-4 w-4" />
        Export
      </button>
      
      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 mt-2 w-48 rounded-md border bg-popover shadow-lg z-50">
            <div className="p-2">
              <button
                onClick={() => handleExport('json')}
                className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm hover:bg-accent"
              >
                <FileJson className="h-4 w-4" />
                Export as JSON
              </button>
              <button
                onClick={() => handleExport('md')}
                className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm hover:bg-accent"
              >
                <FileText className="h-4 w-4" />
                Export as Markdown
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};