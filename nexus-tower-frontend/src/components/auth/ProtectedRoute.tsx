import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { ShieldCheck } from 'lucide-react';

export const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="h-screen w-screen bg-navy-950 flex flex-col items-center justify-center space-y-4">
        <div className="w-12 h-12 rounded-xl bg-navy-900 border border-navy-800 flex items-center justify-center text-brand-cyan shadow-lg animate-pulse">
          <ShieldCheck className="w-6 h-6 text-brand-cyan" />
        </div>
        <div className="text-center">
          <h2 className="text-sm font-semibold text-white tracking-tight">
            Verifying Cognito Authentication...
          </h2>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            AWS Region: ap-south-1
          </p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};
