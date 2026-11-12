export interface CognitoUserSession {
  username: string;
  email?: string;
  idToken?: string;
  accessToken?: string;
  refreshToken?: string;
  isValid: boolean;
}

export interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: CognitoUserSession | null;
  error: string | null;
}

export interface AuthContextType extends AuthState {
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  clearError: () => void;
}
