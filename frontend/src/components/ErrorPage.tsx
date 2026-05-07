import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useSEOMetaTags } from '../hooks/useSEOMetaTags';

interface ErrorPageProps {
  statusCode: 404 | 403;
  title: string;
  description: string;
}

/**
 * Компонент для отображения ошибок 404 и 403
 * Улучшает UX и помогает боту распознать ошибки для правильного SEO
 */
export const ErrorPage: React.FC<ErrorPageProps> = ({ 
  statusCode, 
  title, 
  description 
}) => {
  const navigate = useNavigate();

  useSEOMetaTags({
    title: `${statusCode} - ${title} | AI Ophthalmological Assistant`,
    description: description,
    robotsDirective: 'noindex, follow'
  });

  return (
    <div className="error-page-container" style={styles.container}>
      <div style={styles.errorContent}>
        <h1 style={styles.statusCode}>{statusCode}</h1>
        <h2 style={styles.title}>{title}</h2>
        <p style={styles.description}>{description}</p>
        
        <div style={styles.actions}>
          <button 
            onClick={() => navigate('/')}
            style={styles.primaryButton}
          >
            На главную страницу
          </button>
          <button 
            onClick={() => navigate(-1)}
            style={styles.secondaryButton}
          >
            Вернуться назад
          </button>
        </div>

        <div style={styles.suggestions}>
          <h3>Что вы можете сделать:</h3>
          <ul>
            <li>Проверить URL адрес</li>
            <li>Вернуться на <a href="/">главную страницу</a></li>
            <li>Убедиться, что вы авторизованы для доступа к этой странице</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

// 404 - Not Found
export const NotFoundPage: React.FC = () => (
  <ErrorPage
    statusCode={404}
    title="Страница не найдена"
    description="К сожалению, страница, которую вы ищете, не существует или была удалена."
  />
);

// 403 - Forbidden
export const ForbiddenPage: React.FC = () => (
  <ErrorPage
    statusCode={403}
    title="Доступ запрещён"
    description="У вас недостаточно прав для доступа к этой странице. Пожалуйста, убедитесь, что вы авторизованы."
  />
);

const styles = {
  container: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#f5f5f5',
    padding: '20px'
  } as React.CSSProperties,
  errorContent: {
    textAlign: 'center' as const,
    backgroundColor: 'white',
    padding: '60px 40px',
    borderRadius: '8px',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
    maxWidth: '500px'
  } as React.CSSProperties,
  statusCode: {
    fontSize: '72px',
    fontWeight: 'bold',
    color: '#e74c3c',
    margin: '0 0 20px 0'
  } as React.CSSProperties,
  title: {
    fontSize: '32px',
    color: '#333',
    margin: '0 0 10px 0'
  } as React.CSSProperties,
  description: {
    fontSize: '16px',
    color: '#666',
    marginBottom: '30px',
    lineHeight: '1.6'
  } as React.CSSProperties,
  actions: {
    display: 'flex',
    gap: '10px',
    justifyContent: 'center',
    marginBottom: '30px'
  } as React.CSSProperties,
  primaryButton: {
    padding: '10px 20px',
    backgroundColor: '#3498db',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: 'bold'
  } as React.CSSProperties,
  secondaryButton: {
    padding: '10px 20px',
    backgroundColor: '#ecf0f1',
    color: '#333',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px'
  } as React.CSSProperties,
  suggestions: {
    textAlign: 'left' as const,
    backgroundColor: '#f9f9f9',
    padding: '20px',
    borderRadius: '4px',
    marginTop: '20px'
  } as React.CSSProperties
};
