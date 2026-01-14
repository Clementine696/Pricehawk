'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiFetch, setAuthToken, removeAuthToken, getAuthToken } from '@/lib/api';
import { setUserId, trackLogin, trackLogout } from '@/lib/analytics';

interface User {
  username: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  async function checkAuth() {
    // If no token stored, skip auth check
    const token = getAuthToken();
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      // skipAuthRedirect: true because 401 is expected when not logged in
      const res = await apiFetch('/api/auth/me', { skipAuthRedirect: true });
      if (res.ok) {
        const data = await res.json();
        setUser(data);
        // Set user ID in Google Analytics for logged-in sessions
        setUserId(data.username);
      } else {
        // Token is invalid, clear it
        removeAuthToken();
      }
    } catch (error) {
      // 401 is expected when not logged in, don't log it
      if (error instanceof Error && error.message !== 'Unauthorized') {
        console.error('Auth check failed:', error);
      }
      removeAuthToken();
    } finally {
      setLoading(false);
    }
  }

  async function login(username: string, password: string) {
    const res = await apiFetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });

    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.detail || 'Login failed');
    }

    const data = await res.json();

    // Store token in localStorage
    if (data.token) {
      setAuthToken(data.token);
    }

    setUser({ username: data.username });
    
    // Track login event in Google Analytics
    trackLogin(data.username);
  }

  async function logout() {
    try {
      await apiFetch('/api/auth/logout', {
        method: 'POST',
      });
    } catch (error) {
      // Ignore logout errors
      console.error('Logout error:', error);
    }
    // Always clear token and user state
    removeAuthToken();
    setUser(null);
    
    // Track logout event and clear user ID in Google Analytics
    trackLogout();
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
