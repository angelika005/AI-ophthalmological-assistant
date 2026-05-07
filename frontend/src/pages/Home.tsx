import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useSEOMetaTags } from '../hooks/useSEOMetaTags';
import { useJSONLD } from '../hooks/useJSONLD';
import WeatherWidget from '../components/WeatherWidget';

const Home: React.FC = () => {
    const navigate = useNavigate();

    // ✅ SEO оптимизация: динамические мета-теги
    useSEOMetaTags({
        title: 'Онлайн диагностика глаукомы | AI Ophthalmological Assistant',
        description: 'Используйте ИИ для точной диагностики глаукомы. Революционный сервис для студентов-врачей и офтальмологов. Бесплатно и быстро.',
        canonical: window.location.origin + '/',
        ogTitle: 'AI Ophthalmological Assistant - Диагностика глаукомы с ИИ',
        ogDescription: 'Онлайн сервис для диагностики заболеваний глаз с использованием искусственного интеллекта',
        ogImage: window.location.origin + '/og-image.jpg',
        keywords: 'глаукома, диагностика, ИИ, офтальмология, AI, анализ изображений, медицина',
        robotsDirective: 'index, follow',
        twitterCard: 'summary_large_image'
    });

    // ✅ JSON-LD структурированные данные для главной страницы
    useJSONLD({
        type: 'MedicalService',
        data: {
            name: 'AI Ophthalmological Assistant',
            description: 'Онлайн диагностика глаукомы с использованием искусственного интеллекта',
            url: window.location.origin,
            provider: {
                '@type': 'Organization',
                name: 'AI Ophthalmological Assistant'
            },
            areaServed: 'RU',
            availableLanguage: ['en', 'ru']
        }
    });

    const handleStartClick = (e: React.MouseEvent<HTMLButtonElement>) => {
        e.preventDefault();
        navigate('/registration');
    };

    return (
    <main className="m">
        {/* ✅ Семантический раздел с правильной H1 */}
        <section className="photo-block" role="banner">
            <div className="photo-text">
                <div className="photo-block-main">
                    <h1>Онлайн диагностика заболеваний глаз</h1>
                    <p className="intro-subtitle">Используйте передовые технологии ИИ для точного анализа</p>
                </div>
                <div className="photo-block-button">
                    <button 
                        type="button" 
                        className="start-button" 
                        onClick={handleStartClick}
                        aria-label="Начать использование сервиса"
                    >
                        попробовать сейчас
                        <span className="arrow" aria-hidden="true">&#8594;</span>
                    </button>
                </div>
            </div>
        </section>
        
        <div className="info">
            {/* ✅ Семантический article тег */}
            <article className="common-info">
                <div className="common-info-header">
                    <h2 className="section-title">Для чего нужен VisionX?</h2>
                </div>
                <div className="common-info-main">
                    <p>
                        Студентам-врачам необходим помощник-консультант при постановке диагноза глаукомы по снимку глазного дна,
                        потому что данный диагноз требует высокой точности и комплексного анализа,
                        который сложно осуществить без опыта и специализированных знаний.
                        Диагностика глаукомы невозможна на основе одного лишь осмотра или измерения внутриглазного давления —
                        требуется оценка состояния диска зрительного нерва (наличие и степень экскавации),
                        изменения сосудов, а также динамическое наблюдение за прогрессированием заболевания.
                    </p>
                </div>
            </article>

            {/* ✅ Семантический section для преимуществ */}
            <section className="why-info" aria-labelledby="benefits-heading">
                <div className="why-info-header">
                    <h2 id="benefits-heading" className="section-title">Как наш сервис помогает врачам</h2>
                </div>
                <div className="why-info-body">
                    <div className="item">
                        <div className="circle" aria-hidden="true">1</div>
                        <h3>Распознавание признаков</h3>
                        <div className="text">
                            Распознавать тонкие признаки глаукоматозной атрофии и изменения на глазном дне,
                            которые могут быть незаметны новичкам
                        </div>
                    </div>
                    <div className="item">
                        <div className="circle" aria-hidden="true">2</div>
                        <h3>Интерпретация данных</h3>
                        <div className="text">
                            Интерпретировать сложные данные, включая параметры экскавации,
                            цвет и форму диска зрительного нерва
                        </div>
                    </div>
                    <div className="item">
                        <div className="circle" aria-hidden="true">3</div>
                        <h3>Предотвращение ошибок</h3>
                        <div className="text">
                            Предотвратить ошибки в постановке диагноза,
                            которые могут привести к позднему выявлению болезни и недостаточно эффективному лечению.
                        </div>
                    </div>
                </div>
            </section>

            {/* ✅ Семантический section для функций */}
            <section className="features" aria-labelledby="features-heading">
                <h2 id="features-heading" className="section-title features-title">Наши преимущества</h2>
                <div className="feature">
                    <div className="security-img" role="img" aria-label="Иконка безопасности"></div>
                    <div className="feature-text-header">
                        <h3>Безопасность данных</h3>
                    </div>
                    <div className="feature-text">
                        Мы ценим вашу конфиденциальность
                        и используем только учебные данные для обучения нейросети
                    </div>
                </div>
                <div className="feature">
                    <div className="trustability-img" role="img" aria-label="Иконка надежности"></div>
                    <div className="feature-text-header">
                        <h3>Надежность и устойчивость</h3>
                    </div>
                    <div className="feature-text">
                        Сохранение работоспособности и качества предсказаний
                         в сложных, нестабильных условиях при аномальных данных
                    </div>
                </div>
                <div className="feature">
                    <div className="speed-img" role="img" aria-label="Иконка скорости"></div>
                    <div className="feature-text-header">
                        <h3>Скорость обработки данных</h3>
                    </div>
                    <div className="feature-text">
                        Оперативность реакции важна для приложений в реальном времени
                    </div>
                </div>
            </section>

            {/* ✅ Семантический section для информации об авторе */}
            <section className="about-us" id="about" aria-labelledby="about-heading">
                <h2 id="about-heading" className="section-title">О нас</h2>
                <div className="about-us-info">
                    <p>
                        Привет! Я студент, увлеченный разработкой и созданием собственных проектов.
                        Этот сайт - мой pet-проект, созданный для практики и освоения новых технологий.
                        Он помогает мне развивать навыки и готовиться к профессиональной деятельности.
                    </p>
                    <p>
                        Этот проект - открытая площадка для экспериментов и идей,
                        всегда рада обратной связи и предложениям по улучшению.
                    </p>
                </div>
            </section>

            {/* ✅ Интегрированный внешний API - Погода */}
            <section className="weather-section" aria-label="Погодный виджет">
                <div className="weather-card-shell">
                    <WeatherWidget />
                </div>
            </section>

            {/* ✅ Семантический footer section */}
            <section className="contacts" id="contacts" aria-labelledby="contacts-heading">
                <h2 id="contacts-heading" className="section-title">Контакты</h2>
                <div className="contacts-info">
                    <p>E-mail: <a href="mailto:example@mail.ru">example@mail.ru</a></p>
                    <p>Телефон: <a href="tel:+7XXXXXXXXXX">+7 XXX XXX XX XX</a></p>
                </div>
            </section>
        </div>
    </main>
    );
}

export default Home;
