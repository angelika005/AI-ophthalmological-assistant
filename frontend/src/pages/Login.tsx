import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useSEOMetaTags } from '../hooks/useSEOMetaTags';
import '../styles/Auth.css';

const Login: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  // ✅ SEO оптимизация для страницы входа
  useSEOMetaTags({
    title: 'Вход в аккаунт | AI Ophthalmological Assistant',
    description: 'Войдите в свой аккаунт VisionX для доступа к диагностике глаукомы',
    canonical: window.location.origin + '/login',
    robotsDirective: 'index, follow',
    keywords: 'вход, логин, авторизация, AI Ophthalmological Assistant'
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(username, password);
      navigate('/workzone');
    } catch (err: any) {
      setError(err.message || 'Ошибка входа. Проверьте логин и пароль.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="auth-page">
      <div className="auth-container">
        <article className="auth-box">
          <div className="auth-logo">
            <div className="auth-icon" aria-hidden="true">👁️</div>
            <h1>Добро пожаловать</h1>
            <p className="auth-subtitle">Войдите в свой аккаунт VisionX</p>
          </div>

          {error && <div className="error-message" role="alert">{error}</div>}

          <form onSubmit={handleSubmit} className="auth-form">
            <div className="input-group">
              <label htmlFor="username">Имя пользователя</label>
              <input
                id="username"
                type="text"
                placeholder="Введите имя пользователя"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoComplete="username"
              />
              <span className="input-icon" aria-hidden="true">👤</span>
            </div>

            <div className="input-group">
              <label htmlFor="password">Пароль</label>
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                placeholder="Введите пароль"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
              <span className="input-icon" aria-hidden="true">🔒</span>
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? 'Скрыть пароль' : 'Показать пароль'}
              >
                {showPassword ? '👁️' : '👁️‍🗨️'}
              </button>
            </div>

            <button 
              type="submit" 
              className="auth-button"
              disabled={loading}
            >
              {loading ? 'Вход...' : 'Войти'}
            </button>
          </form>

          <p className="auth-footer">
            Нет аккаунта? <Link to="/registration">Зарегистрироваться</Link>
          </p>
        </article>
      </div>
    </main>
  );
};

export default Login;
