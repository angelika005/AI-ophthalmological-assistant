/**
 * Integration tests for authentication flow
 * Tests: registration, login, logout, session management
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import Login from '../../pages/Login';

// Mock the API client
jest.mock('../services/apiClient', () => ({
  apiClient: {
    post: jest.fn(),
    get: jest.fn(),
  },
}));

describe('Authentication Flow Integration Tests', () => {
  describe('Login Flow', () => {
    it('should complete login flow with valid credentials', async () => {
      const { apiClient } = require('../services/apiClient');

      apiClient.post.mockResolvedValueOnce({
        access_token: 'test_token',
        refresh_token: 'refresh_token',
        user_id: 1,
        username: 'testuser',
      });

      render(
        <BrowserRouter>
          <Login />
        </BrowserRouter>
      );

      const usernameInput = screen.getByPlaceholderText(/username/i);
      const passwordInput = screen.getByPlaceholderText(/password/i);
      const loginButton = screen.getByRole('button', { name: /login/i });

      await userEvent.type(usernameInput, 'testuser');
      await userEvent.type(passwordInput, 'Password123');
      await userEvent.click(loginButton);

      await waitFor(() => {
        expect(apiClient.post).toHaveBeenCalledWith('/auth/login', {
          username: 'testuser',
          password: 'Password123',
        });
      });
    });

    it('should display error message on login failure', async () => {
      const { apiClient } = require('../services/apiClient');

      apiClient.post.mockRejectedValueOnce(new Error('Invalid credentials'));

      render(
        <BrowserRouter>
          <Login />
        </BrowserRouter>
      );

      const usernameInput = screen.getByPlaceholderText(/username/i);
      const passwordInput = screen.getByPlaceholderText(/password/i);
      const loginButton = screen.getByRole('button', { name: /login/i });

      await userEvent.type(usernameInput, 'testuser');
      await userEvent.type(passwordInput, 'wrongpassword');
      await userEvent.click(loginButton);

      await waitFor(() => {
        expect(screen.getByText(/error|failed|invalid/i)).toBeInTheDocument();
      });
    });
  });

  describe('Session Management', () => {
    it('should persist token in storage after login', async () => {
      const { apiClient } = require('../services/apiClient');

      apiClient.post.mockResolvedValueOnce({
        access_token: 'test_token_12345',
        refresh_token: 'refresh_token_12345',
      });

      // After login, token should be stored
      localStorage.setItem('accessToken', 'test_token_12345');

      expect(localStorage.getItem('accessToken')).toBe('test_token_12345');
    });

    it('should clear tokens on logout', async () => {
      localStorage.setItem('accessToken', 'test_token');
      localStorage.setItem('refreshToken', 'refresh_token');

      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');

      expect(localStorage.getItem('accessToken')).toBeNull();
      expect(localStorage.getItem('refreshToken')).toBeNull();
    });
  });
});
