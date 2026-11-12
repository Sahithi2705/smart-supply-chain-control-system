import React from 'react';
import { Database, AlertCircle, RefreshCw, FolderSearch } from 'lucide-react';
import { cn } from '../../utilities/cn';

interface EmptyStateProps {
  title: string;
  description: string;
  sourceCode?: string;
  onRetry?: () => void;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  sourceCode,
  onRetry,
  className,
}) => {
  return (
    <div
      className={cn(
        'bg-navy-900 border border-navy-800 rounded-xl p-10 text-center flex flex-col items-center justify-center max-w-xl mx-auto my-6',
        className
      )}
    >
      <div className="w-12 h-12 rounded-xl bg-navy-850 border border-navy-800 flex items-center justify-center text-slate-400 mb-4 shadow-inner">
        {sourceCode ? (
          <Database className="w-6 h-6 text-brand-cyan/70" />
        ) : (
          <FolderSearch className="w-6 h-6 text-slate-400" />
        )}
      </div>

      <h3 className="text-base font-semibold text-white tracking-tight">{title}</h3>
      <p className="mt-1.5 text-xs text-slate-400 leading-relaxed max-w-md">
        {description}
      </p>

      {sourceCode && (
        <div className="mt-4 flex items-center gap-1.5 px-3 py-1 bg-navy-950 border border-navy-800 rounded-md font-mono text-[11px] text-slate-400">
          <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
          <span>Status code: {sourceCode}</span>
        </div>
      )}

      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-5 inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium bg-navy-800 hover:bg-navy-700 text-slate-200 border border-navy-700 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Re-query Endpoint</span>
        </button>
      )}
    </div>
  );
};
