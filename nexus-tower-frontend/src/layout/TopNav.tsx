import React, { useState, useEffect } from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import {
  Bell,
  User,
  LogOut,
  Activity,
  CheckCircle2,
  XCircle,
  Shield,
  ExternalLink,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { checkApiHealth } from '../services/api';

const ROUTE_TITLES: Record<string, { title: string; subtitle: string }> = {
  '/': { title: 'Overview', subtitle: 'Executive visibility and multi-module control tower telemetry' },
  '/shipments': { title: 'Shipment Tracking', subtitle: 'Real-time logistics events, route progression, and delay variance' },
  '/forecasts': { title: 'Demand Forecasting', subtitle: 'Historical test predictions and multi-model forecast benchmarks' },
  '/inventory': { title: 'Inventory Management', subtitle: 'Simulated inventory positions, buffer stock, and replenishment matrix' },
  '/risk': { title: 'Risk Intelligence', subtitle: 'Disruption scoring, active incident stream, and operational recommendations' },
  '/analytics': { title: 'Analytics', subtitle: 'Integrated multi-cloud telemetry and pipeline status across modules 1–5' },
  '/settings': { title: 'Settings', subtitle: 'Cognito authentication configuration, API connection, and platform runtime' },
};

export const TopNav: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const [apiConnected, setApiConnected] = useState<boolean | null>(null);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  // Poll backend health indicator
  useEffect(() => {
    let isMounted = true;
    async function checkHealth() {
      try {
        const res = await checkApiHealth();
        if (isMounted) setApiConnected(res.connected);
      } catch {
        if (isMounted) setApiConnected(false);
      }
    }
    checkHealth();
    const interval = setInterval(checkHealth, 30000); // 30s heartbeat
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const currentRoute = ROUTE_TITLES[location.pathname] || {
    title: 'Control Tower',
    subtitle: 'NEXUS TOWER Platform',
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="h-16 bg-navy-900/90 backdrop-blur border-b border-navy-800 px-6 flex items-center justify-between sticky top-0 z-20">
      {/* Route Title & Subtitle */}
      <div>
        <h1 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
          {currentRoute.title}
        </h1>
        <p className="text-[11px] text-slate-400 hidden sm:block truncate max-w-lg">
          {currentRoute.subtitle}
        </p>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-3">
        {/* API Health Indicator */}
        <div
          className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-navy-950 border border-navy-800 text-[11px] font-mono"
          title={`Backend API at http://127.0.0.1:8000 is ${
            apiConnected ? 'connected' : apiConnected === false ? 'unreachable' : 'checking...'
          }`}
        >
          {apiConnected === true ? (
            <>
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-emerald-400 font-medium hidden md:inline">API: 127.0.0.1:8000</span>
            </>
          ) : apiConnected === false ? (
            <>
              <span className="w-2 h-2 rounded-full bg-rose-500" />
              <span className="text-rose-400 font-medium hidden md:inline">API Disconnected</span>
            </>
          ) : (
            <>
              <span className="w-2 h-2 rounded-full bg-slate-500" />
              <span className="text-slate-400 hidden md:inline">Connecting...</span>
            </>
          )}
        </div>

        {/* User Profile Menu */}
        <div className="relative">
          <button
            onClick={() => setUserMenuOpen(!userMenuOpen)}
            className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-navy-850 border border-transparent hover:border-navy-700 transition-colors"
          >
            <div className="w-7 h-7 rounded-md bg-navy-800 border border-navy-700 flex items-center justify-center text-slate-200">
              <User className="w-4 h-4 text-brand-cyan" />
            </div>
            <div className="text-left hidden lg:block">
              <div className="text-xs font-medium text-slate-200 truncate max-w-[120px]">
                {user?.username || 'Operator'}
              </div>
              <div className="text-[10px] text-slate-500 font-mono">Cognito Auth</div>
            </div>
          </button>

          {userMenuOpen && (
            <div
              className="absolute right-0 mt-2 w-64 bg-navy-900 border border-navy-800 rounded-xl shadow-xl py-2 z-50 text-xs"
              onMouseLeave={() => setUserMenuOpen(false)}
            >
              <div className="px-4 py-2 border-b border-navy-800/80">
                <div className="text-xs font-semibold text-white truncate">{user?.username}</div>
                <div className="text-[11px] text-slate-400 truncate">{user?.email || 'Authenticated Cognito User'}</div>
                <div className="mt-1 flex items-center gap-1 text-[10px] text-brand-cyan font-mono">
                  <Shield className="w-3 h-3" />
                  <span>Pool: ap-south-1_gqD253QfU</span>
                </div>
              </div>

              <div className="py-1">
                <Link
                  to="/settings"
                  onClick={() => setUserMenuOpen(false)}
                  className="flex items-center gap-2 px-4 py-2 text-slate-300 hover:bg-navy-850 hover:text-white"
                >
                  <Activity className="w-3.5 h-3.5 text-slate-400" />
                  <span>System & Auth Settings</span>
                </Link>
                <a
                  href="http://127.0.0.1:8000/docs"
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center justify-between px-4 py-2 text-slate-300 hover:bg-navy-850 hover:text-white"
                >
                  <span className="flex items-center gap-2">
                    <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
                    <span>FastAPI OpenAPI Docs</span>
                  </span>
                  <span className="font-mono text-[10px] text-slate-500">:8000</span>
                </a>
              </div>

              <div className="border-t border-navy-800/80 pt-1">
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2 px-4 py-2 text-rose-400 hover:bg-rose-500/10 hover:text-rose-300 transition-colors"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>Sign Out</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
