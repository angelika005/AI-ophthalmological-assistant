import React from 'react';
import { Link } from 'react-router-dom';

const Login: React.FC = () => {
  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-header">
          <h2>Вход</h2>
          <p>Войдите в свою учетную запись</p>
        </div>
        <form className="auth-form">
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input 
              type="email" 
              id="email" 
              placeholder="Введите ваш email"
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Пароль</label>
            <input 
              type="password" 
              id="password" 
              placeholder="Введите пароль"
              required
            />
          </div>
          <button type="submit" className="auth-button">
            Войти
          </button>
        </form>
        <div className="auth-footer">
          <p>Нет аккаунта? <Link to="/registration">Зарегистрироваться</Link></p>
        </div>
      </div>
    </div>
  );
}

export default Login;
