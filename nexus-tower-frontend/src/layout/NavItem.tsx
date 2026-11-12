import React from 'react';
import { NavLink } from 'react-router-dom';
import { LucideIcon } from 'lucide-react';
import { cn } from '../utilities/cn';

interface NavItemProps {
  to: string;
  icon: LucideIcon;
  label: string;
  badge?: string | number;
  collapsed?: boolean;
}

export const NavItem: React.FC<NavItemProps> = ({
  to,
  icon: Icon,
  label,
  badge,
  collapsed = false,
}) => {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        cn(
          'flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-all group relative',
          isActive
            ? 'bg-brand-blue/15 text-brand-cyan border border-brand-blue/30 shadow-sm'
            : 'text-slate-400 hover:text-slate-200 hover:bg-navy-850/80',
          collapsed && 'justify-center px-2'
        )
      }
      title={collapsed ? label : undefined}
    >
      <Icon className="w-4 h-4 shrink-0 transition-colors group-hover:text-white" />
      {!collapsed && <span className="truncate">{label}</span>}
      {!collapsed && badge !== undefined && (
        <span className="ml-auto text-[10px] font-mono px-1.5 py-0.5 rounded bg-navy-800 text-slate-300 border border-navy-700/80">
          {badge}
        </span>
      )}
    </NavLink>
  );
};
