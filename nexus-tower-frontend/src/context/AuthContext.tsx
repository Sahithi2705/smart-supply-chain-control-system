import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { AuthContextType, CognitoUserSession } from '../types/auth';
import {
  getStoredSession,
  authenticateWithCognito,
  completeNewPasswordChallenge as cognitoCompleteNewPassword,
  clearPendingChallenge,
  signOutUser,
  AuthResult,
} from '../services/cognito';

export interface ExtendedAuthContextType extends AuthContextType {
  isNewPasswordRequired: boolean;
  challengeUsername: string | null;
  completeNewPassword: (newPassword: string) => Promise<void>;
  cancelChallenge: () => void;
}

const AuthContext = createContext<ExtendedAuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<CognitoUserSession | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [isNewPasswordRequired, setIsNewPasswordRequired] = useState<boolean>(false);
  const [challengeUsername, setChallengeUsername] = useState<string | null>(null);

  // Initialize and check persisted session on mount
  useEffect(() => {
    let mounted = true;
    async function restoreSession() {
      try {
        const session = await getStoredSession();
        if (mounted) {
          if (session && session.isValid) {
            setUser(session);
          } else {
            setUser(null);
          }
        }
      } catch (err) {
        if (mounted) {
          console.error('Failed to restore Cognito session:', err);
          setUser(null);
        }
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    }

    restoreSession();
    return () => {
      mounted = false;
    };
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const result: AuthResult = await authenticateWithCognito(username, password);
      if (result.status === 'NEW_PASSWORD_REQUIRED') {
        setIsNewPasswordRequired(true);
        setChallengeUsername(result.username);
      } else {
        setIsNewPasswordRequired(false);
        setChallengeUsername(null);
        setUser(result.session);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Cognito authentication failed';
      setError(msg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const completeNewPassword = useCallback(async (newPassword: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const session = await cognitoCompleteNewPassword(newPassword);
      setUser(session);
      setIsNewPasswordRequired(false);
      setChallengeUsername(null);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to complete password challenge';
      setError(msg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const cancelChallenge = useCallback(() => {
    clearPendingChallenge();
    setIsNewPasswordRequired(false);
    setChallengeUsername(null);
    setError(null);
  }, []);

  const logout = useCallback(() => {
    cancelChallenge();
    signOutUser();
    setUser(null);
    setError(null);
  }, [cancelChallenge]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated: !!user && user.isValid,
        isLoading,
        user,
        error,
        isNewPasswordRequired,
        challengeUsername,
        login,
        completeNewPassword,
        cancelChallenge,
        logout,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth(): ExtendedAuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
