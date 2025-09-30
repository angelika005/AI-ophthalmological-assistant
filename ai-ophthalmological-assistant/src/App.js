function App() {
  return (
    <div className="App">
      <header className="site-header">
        <div className="container">
            <div className="logo">

            </div>
            <nav className="main-nav">
                <ul>
                    <li><a href="#">Главная</a></li>
                    <li><a href="#">О нас</a></li>
                    <li><a href="#">Контакты</a></li>
                    <li>
                        <div className="auth-buttons">
                            <a href="#" className="login">Вход</a>
                            <span className="separator">/</span>
                            <a href="#" className="register">Регистрация</a>
                        </div>
                    </li>
                </ul>
            </nav>
        </div>
      </header>
      <m>
        <div className="photo-block">
            <div className="photo-text">
                <div className="photo-block-main">
                    <h1>Онлайн</h1>
                    <h1>диагностика</h1>
                    <h1>заболеваний глаз</h1>
                </div>
                <div className="photo-block-button">
                    <button class="start-button">
                        попробовать сейчас
                        <span className="arrow">&#8594;</span>
                    </button>
                </div>
            </div>
        </div>
        <div className="info">
            <div className="common-info">
                <div className="common-info-header">
                    <h3>
                        Для чего нужен VisionX?
                    </h3>
                </div>
                <div className="common-info-main">
                    <h4>
                        Студентам-врачам необходим помощник-консультант при постановке диагноза глаукомы по снимку глазного дна,
                        потому что данный диагноз требует высокой точности и комплексного анализа,
                        который сложно осуществить без опыта и специализированных знаний.
                        Диагностика глаукомы невозможна на основе одного лишь осмотра или измерения внутриглазного давления —
                        требуется оценка состояния диска зрительного нерва (наличие и степень экскавации),
                        изменения сосудов, а также динамическое наблюдение за прогрессированием заболевания.
                    </h4>
                </div>
            </div>
            <div className="why-info">
                <div className="why-info-header">
                    <h3>
                        Помощник консультант помогает
                    </h3>
                </div>
                <div className="why-info-body">
                    <div className="item">
                        <div className="circle">1</div>
                        <div className="text">
                            Распознавать тонкие признаки глаукоматозной атрофии и изменения на глазном дне,
                            которые могут быть незаметны новичкам
                        </div>
                    </div>
                    <div className="item">
                        <div className="circle">2</div>
                        <div className="text">
                            Интерпретировать сложные данные, включая параметры экскавации,
                            цвет и форму диска зрительного нерва
                        </div>
                    </div>
                    <div className="item">
                        <div className="circle">3</div>
                        <div className="text">
                            Предотвратить ошибки в постановке диагноза,
                            которые могут привести к позднему выявлению болезни и недостаточно эффективному лечению.
                        </div>
                    </div>
                </div>
            </div>
        </div>
      </m>
    </div>
  );
}

export default App;
