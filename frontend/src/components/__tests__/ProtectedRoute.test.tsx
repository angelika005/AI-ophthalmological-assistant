/**
 * Unit tests for ProtectedRoute component
 * Tests: authentication checking, role-based access, redirects
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import ProtectedRoute from '../ProtectedRoute';
import { AuthContext } from '../../contexts/AuthContext';

describe('ProtectedRoute Component', () => {
  // Test fixture: Mock authenticated user
  const mockAuthenticatedUser = {
    id: 1,
    username: 'testuser',
    email: 'test@example.com',
    role: 'user',
  };

  // Test fixture: Mock admin user
  const mockAdminUser = {
    id: 2,
    username: 'admin',
    email: 'admin@example.com',
    role: 'admin',
  };

  // Test fixture: Protected component
  const ProtectedComponent = () => <div>Protected Content</div>;

  describe('Authentication Tests', () => {
    it('should render protected content when user is authenticated', () => {
      const contextValue = {
        user: mockAuthenticatedUser,
        isLoading: false,
        error: null,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
      };

      render(
        <BrowserRouter>
          <AuthContext.Provider value={contextValue}>
            <ProtectedRoute>
              <ProtectedComponent />
            </ProtectedRoute>
          </AuthContext.Provider>
        </BrowserRouter>
      );

      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });

    it('should redirect to login when user is not authenticated', () => {
      const contextValue = {
        user: null,
        isLoading: false,
        error: null,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
      };

      render(
        <BrowserRouter>
          <AuthContext.Provider value={contextValue}>
            <ProtectedRoute>
              <ProtectedComponent />
            </ProtectedRoute>
          </AuthContext.Provider>
        </BrowserRouter>
      );

      // Should not render protected content
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });

    it('should show loading state while authenticating', () => {
      const contextValue = {
        user: null,
        isLoading: true,
        error: null,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
      };

      render(
        <BrowserRouter>
          <AuthContext.Provider value={contextValue}>
            <ProtectedRoute>
              <ProtectedComponent />
            </ProtectedRoute>
          </AuthContext.Provider>
        </BrowserRouter>
      );

      // Should show loading indicator or nothing
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });
  });

  describe('Role-Based Access Tests', () => {
    it('should allow admin to access admin-only routes', () => {
      const contextValue = {
        user: mockAdminUser,
        isLoading: false,
        error: null,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
      };

      render(
        <BrowserRouter>
          <AuthContext.Provider value={contextValue}>
            <ProtectedRoute requiredRole="admin">
              <ProtectedComponent />
            </ProtectedRoute>
          </AuthContext.Provider>
        </BrowserRouter>
      );

      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });

    it('should deny regular user access to admin-only routes', () => {
      const contextValue = {
        user: mockAuthenticatedUser,
        isLoading: false,
        error: null,
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
      };

      render(
        <BrowserRouter>
          <AuthContext.Provider value={contextValue}>
            <ProtectedRoute requiredRole="admin">
              <ProtectedComponent />
            </ProtectedRoute>
          </AuthContext.Provider>
        </BrowserRouter>
      );

      // Should not render protected content
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('should handle auth error gracefully', () => {
      const contextValue = {
        user: null,
        isLoading: false,
        error: 'Authentication failed',
        login: jest.fn(),
        logout: jest.fn(),
        register: jest.fn(),
      };

      render(
        <BrowserRouter>
          <AuthContext.Provider value={contextValue}>
            <ProtectedRoute>
              <ProtectedComponent />
            </ProtectedRoute>
          </AuthContext.Provider>
        </BrowserRouter>
      );

      // Should handle error state
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });
  });
});
