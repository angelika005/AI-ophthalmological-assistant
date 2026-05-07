"""
Сервис для получения погоды в Москве
Используется для демонстрации интеграции с внешним API

Используемый API: Open-Meteo (https://open-meteo.com/)
- Полностью бесплатный, без требования API ключа
- Высокая надежность и доступность
- Покрывает всю Россию
"""

import aiohttp
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class WeatherService:
    """
    Сервис для получения погоды Москвы через Open-Meteo API
    """
    
    def __init__(self):
        """Инициализация сервиса"""
        # Координаты Москвы (жестко прописаны)
        self.moscow_lat = 55.75
        self.moscow_lon = 37.62
        
        # API endpoint
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.timeout = 10
        self.max_retries = 3
    
    async def get_weather(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Получить данные погоды для Москвы
        (параметры lat, lon игнорируются - используются координаты Москвы)
        
        Args:
            lat: Широта (не используется)
            lon: Долгота (не используется)
            
        Returns:
            Словарь с данными о погоде или None
        """
        # Используем координаты Москвы вместо переданных
        lat = self.moscow_lat
        lon = self.moscow_lon
        
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    # Запрос к Open-Meteo API
                    params = {
                        'latitude': lat,
                        'longitude': lon,
                        'current': 'temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,pressure_msl',
                        'temperature_unit': 'celsius',
                        'wind_speed_unit': 'ms',
                        'timezone': 'Europe/Moscow'
                    }
                    
                    async with session.get(
                        self.base_url,
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=self.timeout)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            logger.info(f"Weather API response received")
                            normalized = self._normalize_data(data)
                            if normalized:
                                return normalized
                            else:
                                logger.error("Failed to normalize weather data")
                                return None
                        else:
                            logger.warning(f"Weather API returned status {response.status}")
                            if attempt < self.max_retries - 1:
                                await asyncio.sleep(2 ** attempt)
                            continue
                            
            except asyncio.TimeoutError:
                logger.warning(f"Weather API timeout (attempt {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                continue
                
            except aiohttp.ClientError as e:
                logger.warning(f"Weather API client error: {e} (attempt {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                continue
                
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return None
        
        logger.error("Weather API failed after all retries")
        return None
    
    def _normalize_data(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Нормализация ответа Open-Meteo API
        """
        try:
            current = raw_data.get('current', {})
            
            if not current:
                logger.error("No 'current' data in response")
                return None
            
            weather_code = int(current.get('weather_code', 0))
            
            temperature = current.get('temperature_2m')
            humidity = current.get('relative_humidity_2m')
            pressure = current.get('pressure_msl')
            wind_speed = current.get('wind_speed_10m')
            
            if temperature is None or humidity is None:
                logger.error(f"Missing required fields: temp={temperature}, humidity={humidity}")
                return None
            
            weather_main = self._get_weather_main(weather_code)
            weather_description = self._get_weather_description(weather_code)
            
            result = {
                'city': 'Москва',
                'country': 'RU',
                'temperature': temperature,
                'feels_like': temperature,
                'temp_min': temperature,
                'temp_max': temperature,
                'pressure': pressure if pressure else 1013,
                'humidity': humidity,
                'visibility': None,
                'wind_speed': wind_speed if wind_speed else 0,
                'clouds': None,
                'weather_main': weather_main,
                'weather_description': weather_description,
                'weather_icon': '🌦️',
                'timestamp': datetime.now().isoformat(),
                'sunrise': None,
                'sunset': None
            }
            
            logger.info(f"Normalized weather data for Moscow")
            return result
            
        except Exception as e:
            logger.error(f"Error normalizing data: {e}", exc_info=True)
            return None
    
    @staticmethod
    def _get_weather_main(code: int) -> str:
        """Категория погоды по WMO коду"""
        if code == 0:
            return 'Clear'
        elif code in [1, 2]:
            return 'Cloudy'
        elif code == 3:
            return 'Overcast'
        elif code in [45, 48]:
            return 'Fog'
        elif code in [51, 53, 55]:
            return 'Drizzle'
        elif code in [61, 63, 65, 80, 81, 82]:
            return 'Rain'
        elif code in [71, 73, 75, 85, 86]:
            return 'Snow'
        elif code in [95, 96, 99]:
            return 'Thunderstorm'
        else:
            return 'Unknown'
    
    @staticmethod
    def _get_weather_description(code: int) -> str:
        """Описание погоды по WMO коду"""
        descriptions = {
            0: 'Ясно',
            1: 'Частично облачно',
            2: 'Облачно',
            3: 'Пасмурно',
            45: 'Туман',
            48: 'Туман',
            51: 'Морось',
            53: 'Морось',
            55: 'Морось сильная',
            61: 'Дождь',
            63: 'Дождь умеренный',
            65: 'Дождь сильный',
            80: 'Ливень',
            81: 'Ливень умеренный',
            82: 'Ливень сильный',
            85: 'Снег',
            86: 'Снег',
            95: 'Гроза',
            96: 'Гроза с градом',
            99: 'Гроза с градом',
        }
        return descriptions.get(code, 'Неизвестно')


# Глобальный экземпляр сервиса
weather_service = WeatherService()
