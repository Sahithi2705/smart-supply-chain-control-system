import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Settings as SettingsIcon,
  User,
  Shield,
  Key,
  Server,
  LogOut,
  RefreshCw,
  CheckCircle2,
  XCircle,
  ExternalLink,
  Code2,
  Cpu,
  Info,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { checkApiHealth, fetchRoot } from '../services/api';
import { HealthResponse } from '../types/api';

export const SettingsPage: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [rootInfo, setRootInfo] = useState<{ service: string; docs: string; status: string } | null>(null);
  const [checkingApi, setCheckingApi] = useState(false);
  const [apiLatency, setApiLatency] = useState<number | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);

  const testConnection = async () => {
    setCheckingApi(true);
    setApiError(null);
    const start = performance.now();
    try {
      const [hRes, rRes] = await Promise.all([checkApiHealth(), fetchRoot()]);
      const duration = Math.round(performance.now() - start);
      setApiLatency(duration);
      setHealth(hRes.status);
      setRootInfo(rRes);
    } catch (err: unknown) {
      setApiError(err instanceof Error ? err.message : 'API unreachable');
      setHealth(null);
      setApiLatency(null);
    } finally {
      setCheckingApi(false);
    }
  };

  useEffect(() => {
    testConnection();
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Top Header */}
      <div>
        <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
          <span>Platform & Authentication Settings</span>
        </h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Amazon Cognito User Pool session, API endpoint configuration, and infrastructure parameters
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* User Profile & Cognito Session */}
        <div className="bg-navy-900 border border-navy-800 rounded-xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-navy-800 pb-3">
            <h3 className="text-sm font-semibold text-white tracking-tight flex items-center gap-2">
              <User className="w-4 h-4 text-brand-cyan" />
              <span>Operator Session</span>
            </h3>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              ACTIVE
            </span>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <span className="text-[11px] text-slate-400 block uppercase tracking-wider">
                Username / Identity
              </span>
              <span className="font-mono text-white font-semibold text-sm">
                {user?.username || 'operator'}
              </span>
            </div>

            <div>
              <span className="text-[11px] text-slate-400 block uppercase tracking-wider">
                Contact Email
              </span>
              <span className="font-mono text-slate-200">
                {user?.email || 'operator@nexus.internal'}
              </span>
            </div>

            <div>
              <span className="text-[11px] text-slate-400 block uppercase tracking-wider">
                Session Token (JWT)
              </span>
              <div className="font-mono text-[10px] text-slate-400 bg-navy-950 p-2 rounded border border-navy-800/80 break-all select-all">
                {user?.idToken ? `${user.idToken.slice(0, 48)}...` : 'Session authenticated (token active)'}
              </div>
            </div>
          </div>

          <div className="pt-3 border-t border-navy-800 flex items-center justify-between">
            <span className="text-xs text-slate-400">End active session:</span>
            <button
              onClick={handleLogout}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 text-xs font-semibold transition-colors"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Sign Out</span>
            </button>
          </div>
        </div>

        {/* Amazon Cognito User Pool Configuration */}
        <div className="bg-navy-900 border border-navy-800 rounded-xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-navy-800 pb-3">
            <h3 className="text-sm font-semibold text-white tracking-tight flex items-center gap-2">
              <Shield className="w-4 h-4 text-brand-blue" />
              <span>Amazon Cognito Configuration</span>
            </h3>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-navy-950 text-slate-300 border border-navy-800">
              PUBLIC CLIENT
            </span>
          </div>

          <div className="space-y-3 text-xs font-mono">
            <div className="flex items-center justify-between py-1 border-b border-navy-800/60">
              <span className="text-slate-400">AWS Region:</span>
              <span className="text-slate-200">
                {import.meta.env.VITE_COGNITO_REGION || 'ap-south-1'}
              </span>
            </div>

            <div className="flex items-center justify-between py-1 border-b border-navy-800/60">
              <span className="text-slate-400">User Pool ID:</span>
              <span className="text-slate-200">
                {import.meta.env.VITE_COGNITO_USER_POOL_ID || 'ap-south-1_gqD253QfU'}
              </span>
            </div>

            <div className="flex items-center justify-between py-1 border-b border-navy-800/60">
              <span className="text-slate-400">App Client ID:</span>
              <span className="text-slate-200">
                {import.meta.env.VITE_COGNITO_CLIENT_ID || '1h5fsjuph932ie83vdbgol7b3p'}
              </span>
            </div>

            <div className="flex items-center justify-between py-1">
              <span className="text-slate-400">Client Secret:</span>
              <span className="text-emerald-400 font-semibold text-[11px]">
                NONE (PUBLIC APP CLIENT)
              </span>
            </div>
          </div>

          <p className="text-[11px] text-slate-400 leading-relaxed pt-2 border-t border-navy-800/80">
            Complies with AWS security best practice: SPA public client with SRP / USER_PASSWORD_AUTH authentication. No server secret is stored in client bundles.
          </p>
        </div>
      </div>

      {/* Backend API Connection & Heartbeat */}
      <div className="bg-navy-900 border border-navy-800 rounded-xl p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-navy-800 pb-3">
          <div className="flex items-center gap-2">
            <Server className="w-4 h-4 text-brand-cyan" />
            <h3 className="text-sm font-semibold text-white tracking-tight">
              FastAPI Unified Integration Gateway
            </h3>
          </div>

          <button
            onClick={testConnection}
            disabled={checkingApi}
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-navy-850 hover:bg-navy-800 text-xs text-slate-300 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${checkingApi ? 'animate-spin' : ''}`} />
            <span>Ping API</span>
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-mono">
          <div className="p-3 bg-navy-950 border border-navy-800 rounded-lg">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Target URL</span>
            <span className="text-white font-semibold mt-1 block">
              {import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'}
            </span>
          </div>

          <div className="p-3 bg-navy-950 border border-navy-800 rounded-lg">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Connection State</span>
            <div className="flex items-center gap-1.5 mt-1">
              {health ? (
                <>
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span className="text-emerald-400 font-bold">CONNECTED ({apiLatency}ms)</span>
                </>
              ) : (
                <>
                  <XCircle className="w-4 h-4 text-rose-400" />
                  <span className="text-rose-400 font-bold">UNREACHABLE</span>
                </>
              )}
            </div>
          </div>

          <div className="p-3 bg-navy-950 border border-navy-800 rounded-lg">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Backend Version</span>
            <span className="text-white mt-1 block">
              {rootInfo?.service || 'Smart Supply Chain Control Tower API v1.0.0'}
            </span>
          </div>
        </div>

        {apiError && (
          <div className="p-3 bg-rose-950/40 border border-rose-900 rounded-lg text-xs text-rose-300 font-mono">
            {apiError}
          </div>
        )}

        <div className="flex items-center justify-between text-xs text-slate-400 pt-2">
          <span>FastAPI Documentation:</span>
          <a
            href="http://127.0.0.1:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 text-brand-cyan hover:underline"
          >
            <span>Interactive OpenAPI Swagger UI</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>

      {/* Platform Information & Provenance Policy */}
      <div className="bg-navy-900 border border-navy-800 rounded-xl p-5 shadow-sm space-y-3">
        <h3 className="text-sm font-semibold text-white tracking-tight flex items-center gap-2">
          <Code2 className="w-4 h-4 text-slate-400" />
          <span>About NEXUS TOWER Control Tower</span>
        </h3>
        <p className="text-xs text-slate-400 leading-relaxed">
          NEXUS TOWER is an enterprise-grade multi-module supply chain intelligence platform integrating canonical data lakes (Amazon S3 / Glue), event-driven messaging (Apache Kafka), machine learning demand forecasting (Amazon SageMaker / XGBoost), inventory buffer optimization, and automated disruption risk assessment.
        </p>

        <div className="pt-2 flex flex-wrap gap-2 text-[10px] font-mono">
          <span className="px-2 py-0.5 rounded bg-navy-950 text-slate-400 border border-navy-800">
            Frontend: React 18 + Vite 6 + Tailwind CSS
          </span>
          <span className="px-2 py-0.5 rounded bg-navy-950 text-slate-400 border border-navy-800">
            Visualizations: Recharts 2
          </span>
          <span className="px-2 py-0.5 rounded bg-navy-950 text-slate-400 border border-navy-800">
            Security: Amazon Cognito Identity JS
          </span>
          <span className="px-2 py-0.5 rounded bg-navy-950 text-slate-400 border border-navy-800">
            Backend: FastAPI + Uvicorn
          </span>
        </div>
      </div>
    </div>
  );
};
