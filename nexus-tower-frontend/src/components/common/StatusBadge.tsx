import React from 'react';
import { cn } from '../../utilities/cn';
import {
  getRiskBadgeStyle,
  getDelayBadgeStyle,
  getPriorityBadgeStyle,
} from '../../utilities/riskStyles';

interface StatusBadgeProps {
  type: 'risk' | 'delay' | 'priority' | 'custom';
  value: string | null | undefined;
  className?: string;
  showDot?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  type,
  value,
  className,
  showDot = true,
}) => {
  if (!value) return <span className="text-slate-500">—</span>;

  let style = {
    bg: 'bg-slate-500/10',
    text: 'text-slate-400',
    border: 'border-slate-500/20',
    dot: 'bg-slate-500',
  };

  if (type === 'risk') {
    style = getRiskBadgeStyle(value);
  } else if (type === 'delay') {
    style = getDelayBadgeStyle(value);
  } else if (type === 'priority') {
    style = getPriorityBadgeStyle(value);
  }

  // Format display text (e.g., MODERATE_DELAY -> Moderate Delay)
  const formattedText = value
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(' ');

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border font-mono tracking-tight',
        style.bg,
        style.text,
        style.border,
        className
      )}
    >
      {showDot && <span className={cn('w-1.5 h-1.5 rounded-full', style.dot)} />}
      <span>{formattedText}</span>
    </span>
  );
};
