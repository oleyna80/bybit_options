import React from 'react';
import { AlertCircle } from 'lucide-react';

interface ErrorMessageProps {
  message: string;
  title?: string;
  onRetry?: () => void;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({
  message,
  title = 'Error',
  onRetry,
}) => {
  return (
    <div className="rounded-lg border border-danger/20 bg-danger/5 p-4">
      <div className="flex items-start">
        <AlertCircle className="h-5 w-5 text-danger mt-0.5 mr-3" />
        <div className="flex-1">
          <h3 className="font-semibold text-danger">{title}</h3>
          <p className="text-sm text-muted-foreground mt-1">{message}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-3 btn btn-outline btn-sm"
            >
              Try Again
            </button>
          )}
        </div>
      </div>
    </div>
  );
};