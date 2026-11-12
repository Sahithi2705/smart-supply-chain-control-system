import React from 'react';
import { Search, X } from 'lucide-react';
import { cn } from '../../utilities/cn';

interface FilterOption {
  label: string;
  value: string;
}

interface SearchFilterBarProps {
  searchPlaceholder?: string;
  searchTerm: string;
  onSearchChange: (val: string) => void;
  filters?: {
    id: string;
    label: string;
    value: string;
    options: FilterOption[];
    onChange: (val: string) => void;
  }[];
  totalCount?: number;
  filteredCount?: number;
  className?: string;
}

export const SearchFilterBar: React.FC<SearchFilterBarProps> = ({
  searchPlaceholder = 'Search records...',
  searchTerm,
  onSearchChange,
  filters = [],
  totalCount,
  filteredCount,
  className,
}) => {
  return (
    <div
      className={cn(
        'flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 p-3 bg-navy-900 border border-navy-800 rounded-xl',
        className
      )}
    >
      <div className="flex-1 flex items-center gap-2 relative">
        <Search className="w-4 h-4 text-slate-400 absolute left-3 pointer-events-none" />
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder={searchPlaceholder}
          className="w-full bg-navy-950 border border-navy-800 rounded-lg pl-9 pr-8 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-blue"
        />
        {searchTerm && (
          <button
            onClick={() => onSearchChange('')}
            className="absolute right-2.5 text-slate-400 hover:text-white"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {filters.map((filter) => (
          <div key={filter.id} className="flex items-center gap-1.5">
            <span className="text-[11px] text-slate-400 uppercase tracking-wider">{filter.label}:</span>
            <select
              value={filter.value}
              onChange={(e) => filter.onChange(e.target.value)}
              className="bg-navy-950 border border-navy-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-brand-blue"
            >
              {filter.options.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        ))}

        {totalCount !== undefined && (
          <div className="text-[11px] font-mono text-slate-400 px-2 py-1 bg-navy-950 rounded border border-navy-800/80">
            {filteredCount !== undefined && filteredCount !== totalCount
              ? `${filteredCount} / ${totalCount}`
              : `${totalCount} records`}
          </div>
        )}
      </div>
    </div>
  );
};
