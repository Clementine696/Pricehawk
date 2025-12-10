'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiFetch } from '@/lib/api';

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
    try {
      // skipAuthRedirect: true because 401 is expected when not logged in
      const res = await apiFetch('/api/auth/me', { skipAuthRedirect: true });
      if (res.ok) {
        const data = await res.json();
        setUser(data);
      }
    } catch (error) {
      // 401 is expected when not logged in, don't log it
      if (error instanceof Error && error.message !== 'Unauthorized') {
        console.error('Auth check failed:', error);
      }
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
    setUser({ username: data.username });
  }

  async function logout() {
    await apiFetch('/api/auth/logout', {
      method: 'POST',
    });
    setUser(null);
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
