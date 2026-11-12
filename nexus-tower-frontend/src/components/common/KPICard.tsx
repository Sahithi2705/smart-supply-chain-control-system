import React from 'react';
import { LucideIcon } from 'lucide-react';
import { cn } from '../../utilities/cn';

interface KPICardProps {
  title: string;
  value: string | number | null | undefined;
  subtitle?: string;
  icon?: LucideIcon;
  badge?: {
    text: string;
    variant: 'positive' | 'negative' | 'neutral' | 'warning';
  };
  provenance?: string;
  loading?: boolean;
  className?: string;
}

export const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  badge,
  provenance,
  loading = false,
  className,
}) => {
  const badgeClasses = {
    positive: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    negative: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
    warning: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    neutral: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
  };

  return (
    <div
      className={cn(
        'bg-navy-900 border border-navy-800 rounded-xl p-5 shadow-sm hover:border-navy-700 transition-colors',
        className
      )}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wider text-slate-400">
          {title}
        </span>
        {Icon && (
          <div className="p-2 bg-navy-850 border border-navy-800 rounded-lg text-brand-cyan">
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>

      <div className="mt-3 flex items-baseline gap-2">
        {loading ? (
          <div className="h-8 w-24 bg-navy-800 animate-pulse rounded" />
        ) : (
          <span className="text-2xl font-bold tracking-tight text-white font-mono">
            {value !== null && value !== undefined ? value : '—'}
          </span>
        )}

        {badge && !loading && (
          <span
            className={cn(
              'text-xs font-medium px-2 py-0.5 rounded-full border',
              badgeClasses[badge.variant]
            )}
          >
            {badge.text}
          </span>
        )}
      </div>

      {(subtitle || provenance) && (
        <div className="mt-2 flex items-center justify-between text-xs text-slate-400 border-t border-navy-800/60 pt-2">
          {subtitle && <span>{subtitle}</span>}
          {provenance && (
            <span className="text-[10px] text-slate-500 uppercase tracking-wider font-mono">
              {provenance}
            </span>
          )}
        </div>
      )}
    </div>
  );
};
