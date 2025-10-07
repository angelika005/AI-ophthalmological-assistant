const Home = () => {
    return (
    <div className="m">
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
            <div className="features">
                <div className="feature">
                    <div className="security-img"></div>
                    <div className="feature-text-header">
                        <h5>Безопасность данных</h5>
                    </div>
                    <div className="feature-text">
                        Мы ценим вашу конфиденциальность
                        и используем только учебные данные для обучения нейросети
                    </div>
                </div>
                <div className="feature">
                    <div className="trustability-img"></div>
                    <div className="feature-text-header">
                        <h5>Надежность и устойчивость</h5>
                    </div>
                    <div className="feature-text">
                        Сохранение работоспособности и качества предсказаний
                         в сложных, нестабильных условиях при аномальных данных
                    </div>
                </div>
                <div className="feature">
                    <div className="speed-img"></div>
                    <div className="feature-text-header">
                        <h5>Скорость обработки данных</h5>
                    </div>
                    <div className="feature-text">
                        Оперативность реакции важна для приложений в реальном времени
                    </div>
                </div>
            </div>
            <div className="about-us">
                <div className="about-us-header">О нас</div>
                <div className="about-us-info">
                    Привет! Я студент, увлеченный разработкой и созданием собственных проектов.
                    Этот сайт - мой pet-проект, созданный для практики и освоения новых технологий.
                    Он помогает мне развивать навыки и готовиться к профессиональной деятельности.
                    Этот проект - открытая площадка для экспериментов и идей,
                    всегда рада обратной связи и предложениям по улучшению.
                </div>
            </div>
            <div className="contacts">
                <div className="contacts-header">
                    <h3>Контакты</h3>
                </div>
                <div className="contacts-info">
                    <p>E-mail: ....@mail.ru</p>
                    <p>number: ...</p>
                </div>
            </div>
        </div>
    </div>
    );
}

export default Home;