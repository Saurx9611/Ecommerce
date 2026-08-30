'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

type AuthContextType = {
  token: string | null;
  userId: number | null;
  login: (token: string, userId: number) => void;
  logout: () => void;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [userId, setUserId] = useState<number | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const router = useRouter();

  useEffect(() => {
    // Load from local storage on mount
    const storedToken = localStorage.getItem('equinox_token');
    const storedUserId = localStorage.getItem('equinox_user_id');
    if (storedToken && storedUserId) {
      setToken(storedToken);
      setUserId(parseInt(storedUserId));
    }
    setIsLoaded(true);
  }, []);

  const login = (newToken: string, newUserId: number) => {
    setToken(newToken);
    setUserId(newUserId);
    localStorage.setItem('equinox_token', newToken);
    localStorage.setItem('equinox_user_id', newUserId.toString());
    router.push('/');
  };

  const logout = () => {
    setToken(null);
    setUserId(null);
    localStorage.removeItem('equinox_token');
    localStorage.removeItem('equinox_user_id');
    router.push('/login');
  };

  if (!isLoaded) return <div className="hidden" />;

  return (
    <AuthContext.Provider value={{ token, userId, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
