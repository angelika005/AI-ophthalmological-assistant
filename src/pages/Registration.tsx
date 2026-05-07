import React from 'react';
import { Link } from 'react-router-dom';

const Registration: React.FC = () => {
  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-header">
          <h2>Регистрация</h2>
          <p>Создайте новую учетную запись</p>
        </div>
        <form className="auth-form">
          <div className="form-group">
            <label htmlFor="name">Имя</label>
            <input 
              type="text" 
              id="name" 
              placeholder="Введите ваше имя"
              required
            />
          </div>
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
          <div className="form-group">
            <label htmlFor="confirmPassword">Подтвердите пароль</label>
            <input 
              type="password" 
              id="confirmPassword" 
              placeholder="Повторите пароль"
              required
            />
          </div>
          <button type="submit" className="auth-button">
            Зарегистрироваться
          </button>
        </form>
        <div className="auth-footer">
          <p>Уже есть аккаунт? <Link to="/login">Войти</Link></p>
        </div>
      </div>
    </div>
  );
}

export default Registration;
