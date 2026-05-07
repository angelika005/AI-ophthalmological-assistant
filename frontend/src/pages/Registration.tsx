import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useSEOMetaTags } from '../hooks/useSEOMetaTags';
import '../styles/Auth.css';

const Registration: React.FC = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  // ✅ SEO оптимизация для страницы регистрации
  useSEOMetaTags({
    title: 'Регистрация аккаунта | AI Ophthalmological Assistant',
    description: 'Создайте бесплатный аккаунт VisionX и начните использовать диагностику глаукомы на основе ИИ',
    canonical: window.location.origin + '/registration',
    robotsDirective: 'index, follow',
    keywords: 'регистрация, создание аккаунта, AI Ophthalmological Assistant'
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Пароли не совпадают');
      return;
    }

    if (password.length < 6) {
      setError('Пароль должен содержать минимум 6 символов');
      return;
    }

    setLoading(true);

    try {
      await register(username, password, email || undefined);
      navigate('/workzone');
    } catch (err: any) {
      setError(err.message || 'Ошибка регистрации. Попробуйте другое имя пользователя.');
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
            <h1>Регистрация</h1>
            <p className="auth-subtitle">Создайте аккаунт VisionX</p>
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
              <label htmlFor="email">Email (необязательно)</label>
              <input
                id="email"
                type="email"
                placeholder="example@mail.ru"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
              />
              <span className="input-icon" aria-hidden="true">✉️</span>
            </div>

            <div className="input-group">
              <label htmlFor="password">Пароль</label>
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                placeholder="Минимум 6 символов"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="new-password"
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

            <div className="input-group">
              <label htmlFor="confirmPassword">Подтвердите пароль</label>
              <input
                id="confirmPassword"
                type={showPassword ? 'text' : 'password'}
                placeholder="Повторите пароль"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                autoComplete="new-password"
              />
              <span className="input-icon" aria-hidden="true">🔐</span>
            </div>

            <button 
              type="submit" 
              className="auth-button"
              disabled={loading}
            >
              {loading ? 'Регистрация...' : 'Создать аккаунт'}
            </button>
          </form>

          <p className="auth-footer">
            Уже есть аккаунт? <Link to="/login">Войти</Link>
          </p>
        </article>
      </div>
    </main>
  );
};

export default Registration;
