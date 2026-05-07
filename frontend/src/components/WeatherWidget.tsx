import React, { useEffect, useState } from 'react';
import { apiClient } from '../services/apiClient';

interface WeatherData {
  city: string;
  temperature: number;
  humidity: number;
  pressure: number;
  weather_main: string;
  weather_description: string;
  wind_speed: number;
  timestamp: string;
}

interface WeatherResponse {
  success: boolean;
  data: WeatherData | null;
  message: string;
  fallback?: boolean;
}

/**
 * Компонент для отображения информации о погоде Москвы
 * Демонстрирует интеграцию с внешним Open-Meteo API
 * Реализует graceful degradation при недоступности API
 */
const WeatherWidget: React.FC = () => {
  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [fallback, setFallback] = useState(false);

  useEffect(() => {
    const fetchMoscowWeather = async () => {
      // Координаты Москвы
      const moscowLat = 55.7558;
      const moscowLon = 37.6173;
      
      console.log('🌦️ Начало загрузки погоды Москвы...');
      
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);
      
      try {
        const url = `/api/weather?lat=${moscowLat}&lon=${moscowLon}`;
        console.log('📍 URL запроса:', url);

        const response = await apiClient.get(url, { signal: controller.signal });
        clearTimeout(timeoutId);

        console.log('📨 Ответ статус:', response.status);

        const contentType = response.headers.get('content-type') || '';
        if (!contentType.includes('application/json')) {
          throw new Error('Сервер вернул не JSON ответ');
        }

        const data: WeatherResponse = await response.json();
        console.log('📦 Данные:', data);

        if (data.success && data.data) {
          console.log('✅ Погода получена успешно');
          setWeather(data.data);
          setFallback(data.fallback || false);
        } else {
          // Graceful degradation - API недоступен
          console.warn('⚠️ API вернул ошибку:', data.message);
          setError(data.message || 'Не удалось получить данные о погоде Москвы');
          setFallback(true);
        }
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Неизвестная ошибка';
        console.error('❌ Ошибка:', errorMsg);
        setError('Не удалось получить данные о погоде Москвы');
        setFallback(true);
      } finally {
        clearTimeout(timeoutId);
        setLoading(false);
      }
    };

    fetchMoscowWeather();
  }, []);

  if (loading) {
    return (
      <div className="weather-widget loading">
        <p>Загрузка данных о погоде...</p>
      </div>
    );
  }

  if (error && !fallback) {
    return (
      <div className="weather-widget error">
        <p>{error}</p>
      </div>
    );
  }

  if (error && fallback) {
    return (
      <div className="weather-widget fallback">
        <p>{error}</p>
        <p className="info-text">Приложение работает нормально</p>
      </div>
    );
  }

  if (!weather) {
    return null;
  }

  return (
    <div className="weather-widget">
      <div className="weather-header">
        <h3>Погода в Москве</h3>
      </div>
      <div className="weather-content">
        <div className="weather-main">
          <p className="city">{weather.city}</p>
          <p className="temperature">{weather.temperature}°C</p>
          <p className="condition">{weather.weather_main}</p>
        </div>
        
        <div className="weather-details">
          <div className="detail-item">
            <span className="label">💧 Влажность:</span>
            <span className="value">{weather.humidity}%</span>
          </div>
          <div className="detail-item">
            <span className="label">🌬️ Ветер:</span>
            <span className="value">{weather.wind_speed} м/с</span>
          </div>
          <div className="detail-item">
            <span className="label">🔽 Давление:</span>
            <span className="value">{weather.pressure} мбар</span>
          </div>
        </div>

        <p className="weather-note">
          Погодные условия могут влиять на интраокулярное давление и симптомы офтальмологических заболеваний
        </p>
      </div>
    </div>
  );
};

export default WeatherWidget;
