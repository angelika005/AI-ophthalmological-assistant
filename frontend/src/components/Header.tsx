import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Header: React.FC = () => {
    const location = useLocation();
    const isHomePage = location.pathname === '/';
    const isWorkZone = location.pathname === '/workzone';
    const isLoginPage = location.pathname === '/login';
    const isRegisterPage = location.pathname === '/registration';
    const navigate = useNavigate();
    const { isAuthenticated } = useAuth();

    // Функция для обработки клика на логотип
    const handleLogoClick = (e: React.MouseEvent) => {
        if (isHomePage) {
            e.preventDefault(); // Предотвращаем переход по ссылке
            window.scrollTo({ top: 0, behavior: 'smooth' }); // Плавный скролл наверх
        }
        // Если не на главной - ссылка сработает как обычно
    };

    return (
        <header className="site-header">
            <div className="container">
                <nav className="main-nav">
                    <ul>
                        {isHomePage ? (
                            <>
                                <li className="link"><a href="#about">О нас</a></li>
                                <li className="link"><a href="#contacts">Контакты</a></li>
                                <li className="logo-container">
                                    <Link to="/" onClick={handleLogoClick}>
                                        <div className="logo"></div>
                                    </Link>
                                </li>
                                <li className="link">
                                    <Link to="/workzone">Обработка</Link>
                                </li>
                                <li className="link auth-link">
                                    <div className="auth-buttons-vertical">
                                        <Link to="/login" className="login">Вход</Link>
                                        <Link to="/registration" className="register">Регистрация</Link>
                                    </div>
                                </li>
                            </>
                        ) : (
                            <>
                                <li className="link">
                                    <Link to="/workzone">Обработка</Link>
                                </li>
                                <li className="logo-container">
                                    <Link to="/" onClick={handleLogoClick}>
                                        <div className="logo"></div>
                                    </Link>
                                </li>
                                {/* На WorkZone не показываем кнопки Вход/Регистрация */}
                                {!isWorkZone && (
                                    <li className="link auth-link">
                                        <div className="auth-buttons-vertical">
                                            <Link to="/login" className="login">Вход</Link>
                                            <Link to="/registration" className="register">Регистрация</Link>
                                        </div>
                                    </li>
                                )}
                                {/* Кнопка профиля - видна только если авторизован И НЕ на странице логина/регистрации */}
                                {isAuthenticated && !isLoginPage && !isRegisterPage && (
                                    <li className="link">
                                        <button 
                                            onClick={() => navigate('/profile')} 
                                        >
                                            Мой профиль
                                        </button>
                                    </li>
                                )}
                            </>
                        )}
                    </ul>
                </nav>
            </div>
        </header>
    );
}

export default Header;
