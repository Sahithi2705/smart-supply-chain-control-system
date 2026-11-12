export interface BadgeStyle {
  bg: string;
  text: string;
  border: string;
  dot: string;
}

export function getRiskBadgeStyle(level: string | null | undefined): BadgeStyle {
  const norm = (level || '').toUpperCase();
  switch (norm) {
    case 'CRITICAL':
      return {
        bg: 'bg-rose-500/10',
        text: 'text-rose-400',
        border: 'border-rose-500/20',
        dot: 'bg-rose-500',
      };
    case 'HIGH':
      return {
        bg: 'bg-amber-500/10',
        text: 'text-amber-400',
        border: 'border-amber-500/20',
        dot: 'bg-amber-500',
      };
    case 'MEDIUM':
      return {
        bg: 'bg-sky-500/10',
        text: 'text-sky-400',
        border: 'border-sky-500/20',
        dot: 'bg-sky-500',
      };
    case 'LOW':
      return {
        bg: 'bg-emerald-500/10',
        text: 'text-emerald-400',
        border: 'border-emerald-500/20',
        dot: 'bg-emerald-500',
      };
    case 'NORMAL':
      return {
        bg: 'bg-teal-500/10',
        text: 'text-teal-400',
        border: 'border-teal-500/20',
        dot: 'bg-teal-500',
      };
    case 'EXCESS':
      return {
        bg: 'bg-purple-500/10',
        text: 'text-purple-400',
        border: 'border-purple-500/20',
        dot: 'bg-purple-500',
      };
    default:
      return {
        bg: 'bg-slate-500/10',
        text: 'text-slate-400',
        border: 'border-slate-500/20',
        dot: 'bg-slate-500',
      };
  }
}

export function getDelayBadgeStyle(status: string | null | undefined): BadgeStyle {
  const norm = (status || '').toUpperCase();
  switch (norm) {
    case 'ON_TIME':
    case 'NO_DELAY':
      return {
        bg: 'bg-emerald-500/10',
        text: 'text-emerald-400',
        border: 'border-emerald-500/20',
        dot: 'bg-emerald-500',
      };
    case 'MINOR_DELAY':
      return {
        bg: 'bg-blue-500/10',
        text: 'text-blue-400',
        border: 'border-blue-500/20',
        dot: 'bg-blue-500',
      };
    case 'MODERATE_DELAY':
      return {
        bg: 'bg-amber-500/10',
        text: 'text-amber-400',
        border: 'border-amber-500/20',
        dot: 'bg-amber-500',
      };
    case 'SEVERE_DELAY':
    case 'MAJOR_DELAY':
      return {
        bg: 'bg-rose-500/10',
        text: 'text-rose-400',
        border: 'border-rose-500/20',
        dot: 'bg-rose-500',
      };
    default:
      return {
        bg: 'bg-slate-500/10',
        text: 'text-slate-400',
        border: 'border-slate-500/20',
        dot: 'bg-slate-500',
      };
  }
}

export function getPriorityBadgeStyle(priority: string | null | undefined): BadgeStyle {
  const norm = (priority || '').toUpperCase();
  switch (norm) {
    case 'URGENT':
      return {
        bg: 'bg-rose-500/10',
        text: 'text-rose-400',
        border: 'border-rose-500/20',
        dot: 'bg-rose-500',
      };
    case 'HIGH':
      return {
        bg: 'bg-amber-500/10',
        text: 'text-amber-400',
        border: 'border-amber-500/20',
        dot: 'bg-amber-500',
      };
    case 'NORMAL':
    default:
      return {
        bg: 'bg-slate-500/10',
        text: 'text-slate-400',
        border: 'border-slate-500/20',
        dot: 'bg-slate-500',
      };
  }
}
