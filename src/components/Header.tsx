import React from 'react';
import { Link, useLocation } from 'react-router-dom';

const Header: React.FC = () => {
    const location = useLocation();
    const isHomePage = location.pathname === '/';

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
                                    <Link to="/">
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
                                    <Link to="/">
                                        <div className="logo"></div>
                                    </Link>
                                </li>
                                <li className="link auth-link">
                                    <div className="auth-buttons-vertical">
                                        <Link to="/login" className="login">Вход</Link>
                                        <Link to="/registration" className="register">Регистрация</Link>
                                    </div>
                                </li>
                            </>
                        )}
                    </ul>
                </nav>
            </div>
        </header>
    );
}

export default Header;
