export function formatDate(val: string | null | undefined): string {
  if (!val) return '—';
  try {
    const d = new Date(val);
    if (isNaN(d.getTime())) return String(val);
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    }).format(d);
  } catch {
    return String(val);
  }
}

export function formatDateShort(val: string | null | undefined): string {
  if (!val) return '—';
  try {
    const d = new Date(val);
    if (isNaN(d.getTime())) return String(val);
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
    }).format(d);
  } catch {
    return String(val);
  }
}

export function formatNumber(val: number | null | undefined, decimals = 1): string {
  if (val === null || val === undefined) return '—';
  return new Intl.NumberFormat('en-US', {
    maximumFractionDigits: decimals,
    minimumFractionDigits: Number.isInteger(val) ? 0 : decimals,
  }).format(val);
}

export function formatVariance(val: number | null | undefined): { text: string; positive: boolean } {
  if (val === null || val === undefined) return { text: '—', positive: false };
  const sign = val > 0 ? '+' : '';
  return {
    text: `${sign}${val.toFixed(1)}h`,
    positive: val <= 0,
  };
}
