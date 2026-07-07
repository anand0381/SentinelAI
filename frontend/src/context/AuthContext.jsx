import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import { authService } from '../services/authService.js';
import { setUnauthorizedHandler } from '../services/apiClient.js';
import {
  clearStoredSession,
  getStoredToken,
  getStoredUser,
  storeSession,
} from '../utils/storage.js';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUserState] = useState(() => getStoredUser());
  const [token, setToken] = useState(() => getStoredToken());
  const [loading, setLoading] = useState(Boolean(getStoredToken()));
  const [error, setError] = useState('');

  const setUser = useCallback((nextUser) => {
    setUserState(nextUser);

    if (nextUser) {
      const currentToken = getStoredToken();
      if (currentToken) {
        storeSession({ token: currentToken, user: nextUser });
      }
    } else {
      clearStoredSession();
    }
  }, []);

  const setAuthSession = useCallback(({ user: nextUser, token: nextToken }) => {
    setUserState(nextUser);
    setToken(nextToken);
    storeSession({ token: nextToken, user: nextUser });
  }, []);

  const logout = useCallback(() => {
    setUserState(null);
    setToken(null);
    clearStoredSession();
  }, []);

  const refreshCurrentUser = useCallback(async () => {
    const storedToken = getStoredToken();

    if (!storedToken) {
      logout();
      setLoading(false);
      return null;
    }

    setLoading(true);
    setError('');

    try {
      const currentUser = await authService.me();
      setUserState(currentUser);
      setToken(storedToken);
      storeSession({ token: storedToken, user: currentUser });
      return currentUser;
    } catch (requestError) {
      logout();
      setError(requestError.response?.data?.detail || 'Session expired.');
      return null;
    } finally {
      setLoading(false);
    }
  }, [logout]);

  const login = useCallback(async (credentials) => {
    setError('');

    try {
      const session = await authService.login(credentials);
      setAuthSession({
        user: session.user,
        token: session.access_token,
      });
      return session.user;
    } catch (requestError) {
      const message = requestError.response?.data?.detail || 'Unable to sign in.';
      setError(message);
      throw new Error(message);
    }
  }, [setAuthSession]);

  const register = useCallback(async (payload) => {
    setError('');

    try {
      return await authService.register(payload);
    } catch (requestError) {
      const detail = requestError.response?.data?.detail;
      const message = Array.isArray(detail)
        ? detail[0]?.msg || 'Unable to create account.'
        : detail || 'Unable to create account.';
      setError(message);
      throw new Error(message);
    }
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(logout);
    refreshCurrentUser();

    return () => {
      setUnauthorizedHandler(null);
    };
  }, [logout, refreshCurrentUser]);

  const value = useMemo(
    () => ({
      error,
      loading,
      user,
      token,
      isAuthenticated: Boolean(token),
      login,
      logout,
      register,
      refreshCurrentUser,
      setUser,
      setAuthSession,
      clearAuthSession: logout,
    }),
    [
      error,
      loading,
      login,
      logout,
      refreshCurrentUser,
      register,
      setAuthSession,
      setUser,
      user,
      token,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }

  return context;
}
