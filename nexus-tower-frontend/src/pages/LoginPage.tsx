import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  Lock,
  User,
  KeyRound,
  AlertCircle,
  ArrowRight,
  ShieldCheck,
  ChevronLeft,
} from 'lucide-react';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const {
    login,
    completeNewPassword,
    cancelChallenge,
    isNewPasswordRequired,
    challengeUsername,
    isAuthenticated,
    error,
    clearError,
    isLoading,
  } = useAuth();

  // Login form state
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  // First-time login challenge state
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // Form error state
  const [formError, setFormError] = useState<string | null>(null);

  const from = (location.state as any)?.from?.pathname || '/';

  // Navigate to dashboard when authenticated and no challenge pending
  useEffect(() => {
    if (isAuthenticated && !isNewPasswordRequired) {
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, isNewPasswordRequired, navigate, from]);

  // Standard Cognito Login Submission
  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    clearError();

    if (!username.trim()) {
      setFormError('Please enter your Cognito username or email');
      return;
    }
    if (!password) {
      setFormError('Please enter your password');
      return;
    }

    try {
      await login(username, password);
    } catch {
      // Error is set in AuthContext and rendered in error banner
    }
  };

  // NEW_PASSWORD_REQUIRED Challenge Submission
  const handleChallengeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    clearError();

    if (!newPassword) {
      setFormError('Please enter your new permanent password');
      return;
    }
    if (!confirmPassword) {
      setFormError('Please confirm your new permanent password');
      return;
    }
    if (newPassword !== confirmPassword) {
      setFormError('Passwords do not match. Please verify and re-enter.');
      return;
    }
    if (newPassword.length < 8) {
      setFormError('Password must be at least 8 characters long');
      return;
    }

    try {
      await completeNewPassword(newPassword);
    } catch {
      // Error is set in AuthContext and rendered in error banner
    }
  };

  const handleBackToLogin = () => {
    setFormError(null);
    clearError();
    setNewPassword('');
    setConfirmPassword('');
    cancelChallenge();
  };

  return (
    <div className="min-h-screen w-screen bg-navy-950 flex flex-col items-center justify-center p-6 relative overflow-hidden select-none">
      {/* Background ambient accents */}
      <div className="absolute top-1/4 -left-32 w-96 h-96 bg-brand-blue/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 -right-32 w-96 h-96 bg-brand-teal/10 rounded-full blur-3xl pointer-events-none" />

      {/* Main Card */}
      <div className="w-full max-w-md bg-navy-900 border border-navy-800 rounded-2xl p-8 shadow-2xl relative z-10">
        {/* Header Branding */}
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-blue to-brand-cyan flex items-center justify-center text-white font-bold text-lg shadow-sm">
            N
          </div>
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight">NEXUS TOWER</h1>
            <p className="text-xs text-slate-400">Supply Chain Intelligence Platform</p>
          </div>
        </div>

        {/* Dynamic Card Header based on Challenge state */}
        <div className="mb-6 pb-4 border-b border-navy-800">
          {isNewPasswordRequired ? (
            <div>
              <div className="flex items-center gap-2">
                <KeyRound className="w-4 h-4 text-brand-cyan" />
                <h2 className="text-sm font-semibold text-white">
                  First-Login Password Setup
                </h2>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Your account ({challengeUsername || username}) requires a new permanent password before accessing the control tower.
              </p>
            </div>
          ) : (
            <div>
              <h2 className="text-sm font-semibold text-slate-200">
                Control Tower Authentication
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                Sign in via Amazon Cognito User Pool to access telemetry and risk services.
              </p>
            </div>
          )}
        </div>

        {/* Error Banners */}
        {(formError || error) && (
          <div className="mb-5 p-3.5 bg-rose-950/40 border border-rose-900/60 rounded-xl flex items-start gap-2.5 text-xs text-rose-300">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
            <div className="leading-relaxed font-mono">{formError || error}</div>
          </div>
        )}

        {/* Form View: NEW_PASSWORD_REQUIRED Challenge vs Standard Login */}
        {isNewPasswordRequired ? (
          <form onSubmit={handleChallengeSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5 uppercase tracking-wider">
                New Permanent Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full bg-navy-950 border border-navy-800 rounded-lg pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-blue transition-colors"
                  autoComplete="new-password"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5 uppercase tracking-wider">
                Confirm New Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full bg-navy-950 border border-navy-800 rounded-lg pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-blue transition-colors"
                  autoComplete="new-password"
                />
              </div>
            </div>

            <div className="p-3 bg-navy-950 rounded-lg border border-navy-800/80 text-[11px] text-slate-400 space-y-1">
              <div className="flex items-center gap-1.5 text-slate-300 font-medium">
                <ShieldCheck className="w-3.5 h-3.5 text-brand-cyan" />
                <span>Cognito Password Requirements:</span>
              </div>
              <ul className="list-disc list-inside space-y-0.5 text-[10px] text-slate-400 pl-1">
                <li>Minimum 8 characters in length</li>
                <li>At least 1 uppercase letter (A-Z)</li>
                <li>At least 1 lowercase letter (a-z)</li>
                <li>At least 1 numerical digit (0-9) and symbol</li>
              </ul>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full mt-2 py-2.5 px-4 bg-brand-blue hover:bg-blue-600 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-2 shadow-sm transition-colors"
            >
              {isLoading ? (
                <span>Setting Permanent Password...</span>
              ) : (
                <>
                  <span>Set New Password & Access Platform</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>

            <button
              type="button"
              onClick={handleBackToLogin}
              disabled={isLoading}
              className="w-full py-2 px-3 rounded-lg hover:bg-navy-850 text-xs text-slate-400 hover:text-slate-200 flex items-center justify-center gap-1 transition-colors"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
              <span>Back to Sign In</span>
            </button>
          </form>
        ) : (
          <form onSubmit={handleLoginSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5 uppercase tracking-wider">
                Cognito Username / Email
              </label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="operator@nexus.internal"
                  className="w-full bg-navy-950 border border-navy-800 rounded-lg pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-blue transition-colors font-mono"
                  autoComplete="username"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5 uppercase tracking-wider">
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full bg-navy-950 border border-navy-800 rounded-lg pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-blue transition-colors"
                  autoComplete="current-password"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full mt-2 py-2.5 px-4 bg-brand-blue hover:bg-blue-600 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-2 shadow-sm transition-colors"
            >
              {isLoading ? (
                <span>Authenticating with Cognito...</span>
              ) : (
                <>
                  <span>Sign In to Control Tower</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        )}

        {/* AWS Cognito Config Metadata */}
        <div className="mt-8 pt-4 border-t border-navy-800/60 text-[10px] text-slate-500 space-y-1 font-mono">
          <div className="flex items-center justify-between">
            <span>Cognito Region</span>
            <span className="text-slate-400">ap-south-1</span>
          </div>
          <div className="flex items-center justify-between">
            <span>User Pool ID</span>
            <span className="text-slate-400">ap-south-1_gqD253QfU</span>
          </div>
          <div className="flex items-center justify-between">
            <span>Client ID</span>
            <span className="text-slate-400">1h5fsjuph932...</span>
          </div>
          <div className="flex items-center justify-between">
            <span>Backend API</span>
            <span className="text-slate-400">http://127.0.0.1:8000</span>
          </div>
        </div>
      </div>
    </div>
  );
};
