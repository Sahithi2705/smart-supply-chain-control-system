import React from 'react';
import { Info, AlertTriangle, ShieldCheck, Database } from 'lucide-react';
import { cn } from '../../utilities/cn';

interface ProvenanceNoticeProps {
  source?: string;
  provenance?: string;
  note?: string;
  variant?: 'info' | 'warning' | 'neutral' | 'success';
  className?: string;
}

export const ProvenanceNotice: React.FC<ProvenanceNoticeProps> = ({
  source,
  provenance,
  note,
  variant = 'info',
  className,
}) => {
  const styles = {
    info: 'bg-blue-950/40 border-blue-800/50 text-blue-300',
    warning: 'bg-amber-950/40 border-amber-800/50 text-amber-300',
    neutral: 'bg-navy-900 border-navy-800 text-slate-300',
    success: 'bg-emerald-950/40 border-emerald-800/50 text-emerald-300',
  };

  const icons = {
    info: Info,
    warning: AlertTriangle,
    neutral: Database,
    success: ShieldCheck,
  };

  const IconComponent = icons[variant];

  return (
    <div
      className={cn(
        'flex items-start gap-3 p-3.5 rounded-lg border text-xs',
        styles[variant],
        className
      )}
    >
      <IconComponent className="w-4 h-4 mt-0.5 shrink-0 opacity-80" />
      <div className="flex-1 space-y-0.5">
        <div className="font-semibold flex items-center gap-2">
          <span>DATA PROVENANCE NOTICE</span>
          {source && (
            <span className="font-mono text-[10px] uppercase px-1.5 py-0.2 bg-navy-950/60 rounded border border-current opacity-80">
              {source}
            </span>
          )}
        </div>
        {provenance && <p className="opacity-90">{provenance}</p>}
        {note && <p className="opacity-80 italic">{note}</p>}
      </div>
    </div>
  );
};
