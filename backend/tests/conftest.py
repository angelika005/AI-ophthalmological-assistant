"""
Тестовая конфигурация и глобальные фикстуры для всех тестов backend.
Handles:
- Тестовая база данных
- Мокирование внешних сервисов
- Фикстуры пользователей и данных
- JWT токены для тестирования
"""

import pytest
import sys
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
import tempfile
import json

# Добавить parent directory в path для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Важно: переменные окружения должны быть выставлены до импорта main/database,
# иначе приложение попробует подключиться к реальной БД и S3 при загрузке модулей.
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["S3_SKIP_INIT"] = "1"

from main import app
from database import Base, get_db
from models import User, ProcessedImage, Check, UserSession, UserRole
from schemas import UserCreate, Token
from auth import (
    create_access_token,
    generate_refresh_token,
)
import crud


# ============================================================================
# КОНФИГУРАЦИЯ ТЕСТОВОЙ БД
# ============================================================================

@pytest.fixture(scope="session")
def test_db():
    """Создать in-memory SQLite БД для всех тестов"""
    # Используем SQLite in-memory для скорости тестирования
    DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    Base.metadata.create_all(bind=engine)
    yield engine
    
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_db):
    """Создать новую сессию БД для каждого теста"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db)
    session = SessionLocal()

    # Гарантируем чистое состояние БД для каждого теста,
    # так как часть фикстур делает commit().
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()
    
    yield session
    
    # Очистка после теста
    session.rollback()
    session.close()


@pytest.fixture
def client(db_session):
    """FastAPI TestClient с подменой get_db"""
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    test_client = TestClient(app)
    
    yield test_client
    
    app.dependency_overrides.clear()


# ============================================================================
# ФИКСТУРЫ ПОЛЬЗОВАТЕЛЕЙ И ДАННЫХ
# ============================================================================

@pytest.fixture
def test_user_data():
    """Базовые данные для регистрации пользователя"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPassword123!"
    }


@pytest.fixture
def test_admin_data():
    """Базовые данные для администратора"""
    return {
        "username": "admin",
        "email": "admin@example.com",
        "password": "AdminPassword123!"
    }


@pytest.fixture
def regular_user(db_session, test_user_data):
    """Создать обычного пользователя в тестовой БД"""
    user_create = UserCreate(**test_user_data)
    user = crud.create_user(db_session, user_create)
    return user


@pytest.fixture
def admin_user(db_session, test_admin_data):
    """Создать администратора в тестовой БД"""
    user_create = UserCreate(**test_admin_data)
    user = crud.create_user(db_session, user_create)
    user.role = UserRole.ADMIN.value
    db_session.commit()
    return user


@pytest.fixture
def inactive_user(db_session):
    """Создать неактивного пользователя"""
    user = User(
        username="inactive_user",
        email="inactive@example.com",
        password_hash=crud.get_password_hash("Password123"),
        is_active=False
    )
    db_session.add(user)
    db_session.commit()
    return user


# ============================================================================
# ФИКСТУРЫ ТОКЕНОВ И СЕССИЙ
# ============================================================================

@pytest.fixture
def access_token(regular_user):
    """Создать access token для обычного пользователя"""
    return create_access_token(data={"sub": regular_user.username})


@pytest.fixture
def admin_access_token(admin_user):
    """Создать access token для администратора"""
    return create_access_token(data={"sub": admin_user.username})


@pytest.fixture
def refresh_token():
    """Создать refresh token"""
    return generate_refresh_token()


@pytest.fixture
def valid_session(db_session, regular_user, refresh_token):
    """Создать валидную сессию пользователя"""
    session = UserSession(
        user_id=regular_user.id,
        refresh_token=refresh_token,
        device_info="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        ip_address="127.0.0.1",
        is_active=True,
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
    db_session.add(session)
    db_session.commit()
    return session


# ============================================================================
# ФИКСТУРЫ ДЛЯ ОБРАБОТКИ ФАЙЛОВ И ИЗОБРАЖЕНИЙ
# ============================================================================

@pytest.fixture
def test_image_file():
    """Создать тестовый файл изображения (сфабрикованное изображение)"""
    # Создание минимального валидного PNG файла
    png_data = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01'
        b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    return png_data


@pytest.fixture
def processed_image(db_session, regular_user, test_image_file):
    """Создать обработанное изображение в БД"""
    image = ProcessedImage(
        user_id=regular_user.id,
        original_url="s3://bucket/original/image_123.png",
        processed_url="s3://bucket/processed/image_123_processed.png",
        filename="test_image.png",
        file_size=len(test_image_file),
        result="glaucoma",
        glaucoma_probability=0.85,
        status="completed",
        processing_time_ms=2500,
        processed_at=datetime.utcnow()
    )
    db_session.add(image)
    db_session.commit()
    return image


@pytest.fixture
def check_record(db_session, regular_user):
    """Создать запись проверки (Check) в БД"""
    check = Check(
        user_id=regular_user.id,
        title="Glaucoma Check #1",
        content="Diagnosis: Possible glaucoma detected",
        glaucoma_score=0.82,
        status="completed",
        processing_time_ms=3000
    )
    db_session.add(check)
    db_session.commit()
    return check


# ============================================================================
# ФИКСТУРЫ МОКИРОВАНИЯ ВНЕШНИХ СЕРВИСОВ
# ============================================================================

@pytest.fixture
def mock_s3_service():
    """Мокированный S3 сервис"""
    mock_service = Mock()
    mock_service.generate_presigned_url = Mock(
        return_value="https://minio.example.com/presigned-url"
    )
    mock_service.generate_presigned_url_from_stored_url = Mock(
        return_value="https://minio.example.com/presigned-url"
    )
    mock_service.upload_file = Mock(
        return_value="s3://bucket/uploaded/file.png"
    )
    mock_service.delete_file = Mock(return_value=True)
    mock_service.get_object = Mock(
        return_value=b"PNG_FILE_DATA"
    )
    return mock_service


@pytest.fixture
def mock_glaucoma_service():
    """Мокированный ML сервис для глаукомы"""
    mock_service = Mock()
    mock_service.predict = Mock(
        return_value={
            "glaucoma": False,
            "confidence": 0.92,
            "processing_time_ms": 1500
        }
    )
    return mock_service


@pytest.fixture
def mock_weather_service():
    """Мокированный сервис погоды"""
    mock_service = Mock()
    mock_service.get_weather = Mock(
        return_value={
            "temperature": 22.5,
            "condition": "Sunny",
            "humidity": 65,
            "wind_speed": 5
        }
    )
    return mock_service


@pytest.fixture
def patched_s3_service(mock_s3_service):
    """Патчить S3 сервис во всех тестах"""
    with patch('s3_service.s3_service', mock_s3_service):
        with patch('main.s3_service', mock_s3_service):
            yield mock_s3_service


@pytest.fixture
def patched_glaucoma_service(mock_glaucoma_service):
    """Патчить ML сервис во всех тестах"""
    with patch('ml_service.glaucoma_service', mock_glaucoma_service):
        with patch('main.glaucoma_service', mock_glaucoma_service):
            yield mock_glaucoma_service


@pytest.fixture
def patched_weather_service(mock_weather_service):
    """Патчить Weather API сервис во всех тестах"""
    with patch('weather_service.weather_service', mock_weather_service):
        with patch('main.weather_service', mock_weather_service):
            yield mock_weather_service


# ============================================================================
# ФИКСТУРЫ ДЛЯ HTTP ЗАГОЛОВКОВ И ПАРАМЕТРОВ
# ============================================================================

@pytest.fixture
def auth_headers(access_token):
    """HTTP headers для аутентифицированного запроса"""
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }


@pytest.fixture
def admin_auth_headers(admin_access_token):
    """HTTP headers для администратора"""
    return {
        "Authorization": f"Bearer {admin_access_token}",
        "Content-Type": "application/json"
    }


@pytest.fixture
def cookies_with_token(access_token):
    """Cookie с access токеном"""
    return {"access_token": access_token}


# ============================================================================
# УТИЛИТЫ ДЛЯ ТЕСТИРОВАНИЯ
# ============================================================================

def create_test_user(db_session, username="testuser", email="test@example.com", password="Test123"):
    """Утилита для создания тестового пользователя"""
    user_data = UserCreate(username=username, email=email, password=password)
    return crud.create_user(db_session, user_data)


def create_test_admin(db_session, username="admin", email="admin@example.com", password="Admin123"):
    """Утилита для создания тестового администратора"""
    user = create_test_user(db_session, username, email, password)
    user.role = UserRole.ADMIN.value
    db_session.commit()
    return user


@pytest.fixture
def create_user_helper(db_session):
    """Фикстура-функция для создания пользователя в тестах"""
    def _create_user(username="user", email="user@example.com", password="Password123"):
        return create_test_user(db_session, username, email, password)
    return _create_user


@pytest.fixture
def create_admin_helper(db_session):
    """Фикстура-функция для создания администратора в тестах"""
    def _create_admin(username="admin", email="admin@example.com", password="Password123"):
        return create_test_admin(db_session, username, email, password)
    return _create_admin


# ============================================================================
# МАРКЕРЫ И КОНФИГУРАЦИЯ PYTEST
# ============================================================================

def pytest_configure(config):
    """Регистрация пользовательских маркеров"""
    config.addinivalue_line("markers", "unit: Unit tests for functions/methods")
    config.addinivalue_line("markers", "integration: Integration tests for endpoints")
    config.addinivalue_line("markers", "e2e: End-to-end tests for scenarios")
    config.addinivalue_line("markers", "fast: Tests that execute quickly")
    config.addinivalue_line("markers", "slow: Tests that take longer to execute")
    config.addinivalue_line("markers", "critical: Tests for critical business logic")
    config.addinivalue_line("markers", "auth: Tests related to authentication")
    config.addinivalue_line("markers", "admin: Tests for admin functionality")
    config.addinivalue_line("markers", "security: Security-related tests")


# ============================================================================
# ПАРАМЕТРИЗОВАННЫЕ ФИКСТУРЫ
# ============================================================================

@pytest.fixture(
    params=[
        ("user@example.com", True),
        ("admin@example.com", True),
        ("invalid-email", False),
        ("", False),
    ]
)
def email_variants(request):
    """Параметризованная фикстура для различных вариантов email"""
    return request.param


@pytest.fixture(
    params=[
        ("validuser", True),
        ("a" * 50, True),
        ("ab", False),  # Слишком короткое
        ("a" * 51, False),  # Слишком длинное
        ("", False),
    ]
)
def username_variants(request):
    """Параметризованная фикстура для различных вариантов username"""
    return request.param


@pytest.fixture(
    params=[
        ("StrongPass123!", True),
        ("Password123", True),
        ("weak", False),  # Слишком короткое
        ("nouppercase123", False),  # Нет заглавной буквы
        ("NOLOWERCASE123", False),  # Нет строчной буквы
    ]
)
def password_variants(request):
    """Параметризованная фикстура для различных вариантов пароля"""
    return request.param
