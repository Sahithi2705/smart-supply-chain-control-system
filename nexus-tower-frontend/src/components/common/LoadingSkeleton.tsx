import React from 'react';
import { cn } from '../../utilities/cn';

export const LoadingSkeleton: React.FC<{ rows?: number; className?: string }> = ({
  rows = 5,
  className,
}) => {
  return (
    <div className={cn('space-y-3 animate-pulse', className)}>
      <div className="h-6 bg-navy-800 rounded w-1/4" />
      <div className="space-y-2">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="h-10 bg-navy-900 border border-navy-800 rounded-lg w-full" />
        ))}
      </div>
    </div>
  );
};
