import {
  CognitoUserPool,
  CognitoUser,
  AuthenticationDetails,
  CognitoUserSession as AWSCognitoSession,
} from 'amazon-cognito-identity-js';
import { CognitoUserSession } from '../types/auth';

const POOL_DATA = {
  UserPoolId: (import.meta.env.VITE_COGNITO_USER_POOL_ID as string) || 'ap-south-1_gqD253QfU',
  ClientId: (import.meta.env.VITE_COGNITO_CLIENT_ID as string) || '1h5fsjuph932ie83vdbgol7b3p',
};

export const userPool = new CognitoUserPool(POOL_DATA);

export interface AuthSuccessResult {
  status: 'SUCCESS';
  session: CognitoUserSession;
}

export interface AuthChallengeResult {
  status: 'NEW_PASSWORD_REQUIRED';
  username: string;
  userAttributes?: Record<string, any> | null;
  requiredAttributes?: string[];
}

export type AuthResult = AuthSuccessResult | AuthChallengeResult;

// In-memory challenge state — strictly held in memory, never persisted to localStorage
let pendingChallengeUser: CognitoUser | null = null;
let pendingUserAttributes: Record<string, any> | null = null;
let pendingRequiredAttributes: string[] | null = null;

export function getStoredSession(): Promise<CognitoUserSession | null> {
  return new Promise((resolve) => {
    const currentUser = userPool.getCurrentUser();
    if (!currentUser) {
      return resolve(null);
    }

    currentUser.getSession((err: Error | null, session: AWSCognitoSession | null) => {
      if (err || !session || !session.isValid()) {
        return resolve(null);
      }

      const idToken = session.getIdToken().getJwtToken();
      const accessToken = session.getAccessToken().getJwtToken();
      const payload = session.getIdToken().decodePayload();

      resolve({
        username: currentUser.getUsername(),
        email: payload.email,
        idToken,
        accessToken,
        isValid: true,
      });
    });
  });
}

export function authenticateWithCognito(
  username: string,
  password: string
): Promise<AuthResult> {
  return new Promise((resolve, reject) => {
    // Reset any prior in-memory challenge reference
    pendingChallengeUser = null;
    pendingUserAttributes = null;
    pendingRequiredAttributes = null;

    const authenticationData = {
      Username: username.trim(),
      Password: password,
    };
    const authenticationDetails = new AuthenticationDetails(authenticationData);

    const userData = {
      Username: username.trim(),
      Pool: userPool,
    };
    const cognitoUser = new CognitoUser(userData);

    cognitoUser.authenticateUser(authenticationDetails, {
      onSuccess: (result: AWSCognitoSession) => {
        const payload = result.getIdToken().decodePayload();
        const session: CognitoUserSession = {
          username: cognitoUser.getUsername(),
          email: payload.email,
          idToken: result.getIdToken().getJwtToken(),
          accessToken: result.getAccessToken().getJwtToken(),
          isValid: true,
        };
        resolve({
          status: 'SUCCESS',
          session,
        });
      },
      onFailure: (err) => {
        reject(err);
      },
      newPasswordRequired: (userAttributes: any, requiredAttributes: any) => {
        // Intercept FORCE_CHANGE_PASSWORD challenge and retain CognitoUser in memory
        pendingChallengeUser = cognitoUser;
        pendingUserAttributes = userAttributes || {};
        pendingRequiredAttributes = Array.isArray(requiredAttributes) ? requiredAttributes : [];

        resolve({
          status: 'NEW_PASSWORD_REQUIRED',
          username: cognitoUser.getUsername(),
          userAttributes: pendingUserAttributes,
          requiredAttributes: pendingRequiredAttributes,
        });
      },
    });
  });
}

export function completeNewPasswordChallenge(
  newPassword: string
): Promise<CognitoUserSession> {
  return new Promise((resolve, reject) => {
    if (!pendingChallengeUser) {
      return reject(
        new Error('No active password challenge session found. Please sign in again.')
      );
    }

    // Include any required attributes defined by User Pool schema
    const requiredAttributeData: Record<string, string> = {};
    if (pendingRequiredAttributes && pendingRequiredAttributes.length > 0) {
      for (const attr of pendingRequiredAttributes) {
        if (pendingUserAttributes && pendingUserAttributes[attr]) {
          requiredAttributeData[attr] = pendingUserAttributes[attr];
        }
      }
    }

    const targetUser = pendingChallengeUser;

    targetUser.completeNewPasswordChallenge(newPassword, requiredAttributeData, {
      onSuccess: (result: AWSCognitoSession) => {
        const payload = result.getIdToken().decodePayload();
        const session: CognitoUserSession = {
          username: targetUser.getUsername(),
          email: payload.email,
          idToken: result.getIdToken().getJwtToken(),
          accessToken: result.getAccessToken().getJwtToken(),
          isValid: true,
        };

        // Clear in-memory challenge references upon successful completion
        pendingChallengeUser = null;
        pendingUserAttributes = null;
        pendingRequiredAttributes = null;

        resolve(session);
      },
      onFailure: (err) => {
        reject(err);
      },
    });
  });
}

export function clearPendingChallenge(): void {
  pendingChallengeUser = null;
  pendingUserAttributes = null;
  pendingRequiredAttributes = null;
}

export function signOutUser(): void {
  clearPendingChallenge();
  const currentUser = userPool.getCurrentUser();
  if (currentUser) {
    currentUser.signOut();
  }
}
