import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiClient } from '../services/apiClient';

interface User {
  id: number;
  username: string;
  email?: string;
  token: string;
  role: 'user' | 'admin';
  is_active: boolean;
}

interface AuthContextType {
  user: User | null;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string, email?: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Проверка сохраненной сессии при загрузке
  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
    setIsLoading(false);
  }, []);

  // Слушатель на auth-error event из apiClient
  useEffect(() => {
    const handleAuthError = (event: Event) => {
      const customEvent = event as CustomEvent;
      console.warn('Auth error detected:', customEvent.detail);
      
      // Очищаем состояние при ошибке аутентификации
      setUser(null);
      localStorage.removeItem('user');
    };

    window.addEventListener('auth-error', handleAuthError);

    return () => {
      window.removeEventListener('auth-error', handleAuthError);
    };
  }, []);

  const login = async (username: string, password: string) => {
    try {
      const response = await apiClient.post('/api/users/login', {
        username,
        password,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Login failed');
      }

      const data = await response.json();
      
      const userInfoResponse = await apiClient.get('/api/users/me');

      let userData: User;
      if (userInfoResponse.ok) {
        const userInfo = await userInfoResponse.json();
        userData = {
          id: userInfo.id,
          username: userInfo.username,
          email: userInfo.email,
          token: data.access_token,
          role: userInfo.role || 'user',
          is_active: userInfo.is_active ?? true,
        };
      } else {
        userData = {
          id: data.user_id,
          username: data.username,
          email: undefined,
          token: data.access_token,
          role: 'user',
          is_active: true,
        };
      }

      setUser(userData);
      localStorage.setItem('user', JSON.stringify(userData));
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  };

  const register = async (username: string, password: string, email?: string) => {
    try {
      const response = await apiClient.post('/api/users/register', {
        username,
        password,
        email,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Registration failed');
      }

      await login(username, password);
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      await apiClient.post('/api/users/logout');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      localStorage.removeItem('user');
      localStorage.removeItem('access_token_time');
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        login,
        register,
        logout,
        isAuthenticated: !!user,
        isLoading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
