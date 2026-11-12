import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { cn } from '../../utilities/cn';

interface ErrorAlertProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorAlert: React.FC<ErrorAlertProps> = ({
  title = 'API Communication Error',
  message,
  onRetry,
  className,
}) => {
  return (
    <div
      className={cn(
        'p-4 bg-rose-950/40 border border-rose-900/60 rounded-xl flex items-start gap-3 text-rose-200',
        className
      )}
    >
      <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
      <div className="flex-1">
        <h4 className="text-sm font-semibold text-rose-300">{title}</h4>
        <p className="mt-1 text-xs text-rose-200/90 leading-relaxed font-mono">{message}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-3 inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-rose-900/60 hover:bg-rose-900 text-xs font-medium text-rose-100 transition-colors"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Retry Connection</span>
          </button>
        )}
      </div>
    </div>
  );
};
