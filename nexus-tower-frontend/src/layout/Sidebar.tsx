import React from 'react';
import {
  LayoutDashboard,
  Truck,
  TrendingUp,
  Boxes,
  AlertTriangle,
  BarChart3,
  Settings,
  ChevronLeft,
  ChevronRight,
  ShieldAlert,
} from 'lucide-react';
import { NavItem } from './NavItem';
import { cn } from '../utilities/cn';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ collapsed, onToggle }) => {
  const navLinks = [
    { to: '/', label: 'Overview', icon: LayoutDashboard },
    { to: '/shipments', label: 'Shipment Tracking', icon: Truck },
    { to: '/forecasts', label: 'Demand Forecasting', icon: TrendingUp },
    { to: '/inventory', label: 'Inventory Management', icon: Boxes },
    { to: '/risk', label: 'Risk Intelligence', icon: AlertTriangle },
    { to: '/analytics', label: 'Analytics', icon: BarChart3 },
    { to: '/settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside
      className={cn(
        'h-screen bg-navy-900 border-r border-navy-800 flex flex-col transition-all duration-200 z-30 select-none shrink-0',
        collapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Platform Branding */}
      <div className="h-16 px-4 border-b border-navy-800 flex items-center justify-between">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-blue to-brand-cyan flex items-center justify-center text-white font-bold text-base shadow-sm shrink-0">
            N
          </div>
          {!collapsed && (
            <div className="flex flex-col min-w-0">
              <span className="text-sm font-bold tracking-tight text-white truncate">
                NEXUS TOWER
              </span>
              <span className="text-[10px] text-slate-400 font-medium tracking-wide truncate">
                Supply Chain Intelligence
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Navigation Sections */}
      <div className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
        <div className={cn('px-2 mb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-500', collapsed && 'hidden')}>
          Control Tower Modules
        </div>
        {navLinks.map((link) => (
          <NavItem
            key={link.to}
            to={link.to}
            label={link.label}
            icon={link.icon}
            collapsed={collapsed}
          />
        ))}
      </div>

      {/* System Environment Provenance Badge */}
      {!collapsed && (
        <div className="p-3 mx-2 mb-2 rounded-lg bg-navy-950/80 border border-navy-800 text-[11px] text-slate-400 space-y-1">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-slate-300">Environment</span>
            <span className="text-[10px] font-mono px-1 rounded bg-navy-800 text-brand-cyan border border-brand-cyan/20">
              HYBRID-LAKE
            </span>
          </div>
          <div className="text-[10px] text-slate-500 leading-tight">
            Amazon EKS / S3 • SageMaker • FastAPI
          </div>
        </div>
      )}

      {/* Collapse Toggle Footer */}
      <div className="p-2 border-t border-navy-800 flex items-center justify-between">
        <button
          onClick={onToggle}
          className="w-full flex items-center justify-center p-2 rounded-lg hover:bg-navy-850 text-slate-400 hover:text-slate-200 transition-colors"
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <div className="w-full flex items-center justify-between px-2 text-xs">
              <span>Collapse Sidebar</span>
              <ChevronLeft className="w-4 h-4" />
            </div>
          )}
        </button>
      </div>
    </aside>
  );
};
