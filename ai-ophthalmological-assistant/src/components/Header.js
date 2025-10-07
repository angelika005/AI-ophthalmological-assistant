function Header() {
    return (
        <header className="site-header">
            <div className="container">
                <nav className="main-nav">
                    <ul>
                        <li className="buttons"><a href="/about_us">О нас</a></li>
                        <li className="/contacts"><a href="#">Контакты</a></li>
                        <li><div className="logo"></div></li>
                        <li className="buttons"><a href="/">Главная</a></li>
                        <li className="buttons">
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