function Header() {
    return (
        <header className="site-header">
            <div className="container">
                <nav className="main-nav">
                    <ul>
                        <li className="link"><a href="/about_us">О нас</a></li>
                        <li className="link"><a href="/contacts">Контакты</a></li>
                        <li><div className="logo"></div></li>
                        <li className="link"><a href="/">Главная</a></li>
                        <li className="link">
                            <div className="auth-buttons">
                                <a href="/login" className="login">Вход</a>
                                <span className="separator">/</span>
                                <a href="/sign_in" className="register">Регистрация</a>
                            </div>
                        </li>
                    </ul>
                </nav>
            </div>
        </header>
    );
}

export default Header