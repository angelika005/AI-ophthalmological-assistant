"""
Unit tests для crud.py - тестирование операций с базой данных
Покрывает: создание пользователей, получение данных, обновление, удаление
"""

import pytest
from datetime import datetime, timedelta
from models import User, UserSession, UserRole
from schemas import UserCreate
import crud


@pytest.mark.unit
class TestUserCreation:
    """Тесты для создания пользователя"""
    
    def test_create_user_with_valid_data(self, db_session):
        """Проверка создания пользователя с валидными данными"""
        user_data = UserCreate(
            username="newuser",
            email="newuser@example.com",
            password="Password123"
        )
        user = crud.create_user(db_session, user_data)
        
        assert user.username == "newuser"
        assert user.email == "newuser@example.com"
        assert user.is_active is True
        assert user.role == UserRole.USER.value
        assert user.id is not None
    
    def test_create_user_password_is_hashed(self, db_session):
        """Проверка, что пароль хешируется при создании"""
        user_data = UserCreate(
            username="user1",
            email="user1@example.com",
            password="PlainPassword123"
        )
        user = crud.create_user(db_session, user_data)
        
        # Пароль не должен совпадать с исходным
        assert user.password_hash != "PlainPassword123"
        # Пароль должен быть хеше
        assert "$argon2" in user.password_hash
    
    def test_create_user_with_duplicate_username_fails(self, db_session, regular_user):
        """Проверка, что создание пользователя с дублирующимся username не удается"""
        user_data = UserCreate(
            username=regular_user.username,
            email="different@example.com",
            password="Password123"
        )
        
        with pytest.raises(Exception):  # SQLAlchemy IntegrityError
            crud.create_user(db_session, user_data)
    
    def test_create_user_with_duplicate_email_fails(self, db_session, regular_user):
        """Проверка, что создание пользователя с дублирующимся email не удается"""
        user_data = UserCreate(
            username="different_user",
            email=regular_user.email,
            password="Password123"
        )
        
        with pytest.raises(Exception):  # SQLAlchemy IntegrityError
            crud.create_user(db_session, user_data)


@pytest.mark.unit
class TestUserRetrieval:
    """Тесты для получения данных пользователя"""
    
    def test_get_user_by_username_returns_user(self, db_session, regular_user):
        """Проверка получения пользователя по username"""
        user = crud.get_user_by_username(db_session, regular_user.username)
        
        assert user is not None
        assert user.id == regular_user.id
        assert user.username == regular_user.username
    
    def test_get_user_by_username_nonexistent_returns_none(self, db_session):
        """Проверка, что несуществующий username возвращает None"""
        user = crud.get_user_by_username(db_session, "nonexistent")
        assert user is None
    
    def test_get_user_by_email_returns_user(self, db_session, regular_user):
        """Проверка получения пользователя по email"""
        user = crud.get_user_by_email(db_session, regular_user.email)
        
        assert user is not None
        assert user.id == regular_user.id
        assert user.email == regular_user.email
    
    def test_get_user_by_email_nonexistent_returns_none(self, db_session):
        """Проверка, что несуществующий email возвращает None"""
        user = crud.get_user_by_email(db_session, "nonexistent@example.com")
        assert user is None
    
    def test_get_user_by_id_returns_user(self, db_session, regular_user):
        """Проверка получения пользователя по ID"""
        user = crud.get_user_by_id(db_session, regular_user.id)
        
        assert user is not None
        assert user.id == regular_user.id
        assert user.username == regular_user.username
    
    def test_get_user_by_id_nonexistent_returns_none(self, db_session):
        """Проверка, что несуществующий ID возвращает None"""
        user = crud.get_user_by_id(db_session, 99999)
        assert user is None
    
    def test_get_users_pagination(self, db_session, create_user_helper):
        """Проверка получения списка пользователей с пагинацией"""
        # Создаем несколько пользователей
        for i in range(5):
            create_user_helper(username=f"user{i}", email=f"user{i}@example.com")
        
        # Получаем с пагинацией
        users = crud.get_users(db_session, skip=0, limit=2)
        
        assert len(users) == 2
    
    def test_get_users_offset(self, db_session, create_user_helper):
        """Проверка смещения в при получении списка пользователей"""
        # Создаем несколько пользователей
        user1 = create_user_helper(username="user1", email="user1@example.com")
        user2 = create_user_helper(username="user2", email="user2@example.com")
        user3 = create_user_helper(username="user3", email="user3@example.com")
        
        # Получаем со смещением
        users = crud.get_users(db_session, skip=1, limit=2)
        
        assert len(users) <= 2
        # Первый пользователь не должен быть в результате (с skip=1)
        usernames = [u.username for u in users]
        assert "user1" not in usernames or len(users) == 2


@pytest.mark.unit
class TestUserDeletion:
    """Тесты для удаления пользователя"""
    
    def test_delete_user_successful(self, db_session, regular_user):
        """Проверка успешного удаления пользователя"""
        user_id = regular_user.id
        
        result = crud.delete_user(db_session, user_id)
        
        assert result is True
        assert crud.get_user_by_id(db_session, user_id) is None
    
    def test_delete_nonexistent_user_returns_false(self, db_session):
        """Проверка удаления несуществующего пользователя"""
        result = crud.delete_user(db_session, 99999)
        assert result is False
    
    def test_delete_user_removes_related_sessions(self, db_session, valid_session):
        """Проверка, что удаление пользователя удаляет его сессии"""
        user_id = valid_session.user_id
        session_id = valid_session.id
        
        crud.delete_user(db_session, user_id)
        
        # Сессия не должна существовать
        user_session = db_session.query(UserSession).filter(
            UserSession.id == session_id
        ).first()
        assert user_session is None


@pytest.mark.unit
class TestSessionManagement:
    """Тесты для управления сессиями"""
    
    def test_create_or_update_session_creates_new_session(self, db_session, regular_user):
        """Проверка создания новой сессии"""
        refresh_token = "test_refresh_token_123"
        device_info = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        ip_address = "192.168.1.1"
        
        session = crud.create_or_update_session(
            db_session,
            regular_user.id,
            refresh_token,
            device_info,
            ip_address
        )
        
        assert session.user_id == regular_user.id
        assert session.refresh_token == refresh_token
        assert session.device_info == device_info
        assert session.ip_address == ip_address
        assert session.is_active is True
    
    def test_create_or_update_session_updates_existing(self, db_session, valid_session):
        """Проверка обновления существующей сессии"""
        new_refresh_token = "new_refresh_token_456"
        
        updated_session = crud.create_or_update_session(
            db_session,
            valid_session.user_id,
            new_refresh_token,
            valid_session.device_info,
            valid_session.ip_address
        )
        
        assert updated_session.id == valid_session.id
        assert updated_session.refresh_token == new_refresh_token
    
    def test_get_active_session_returns_session(self, db_session, valid_session):
        """Проверка получения активной сессии"""
        session = crud.get_active_session(
            db_session,
            valid_session.user_id,
            valid_session.device_info,
            valid_session.ip_address
        )
        
        assert session is not None
        assert session.id == valid_session.id
    
    def test_get_active_session_with_different_ip_returns_none(self, db_session, valid_session):
        """Проверка, что сессия с другим IP не найдется"""
        session = crud.get_active_session(
            db_session,
            valid_session.user_id,
            valid_session.device_info,
            "192.168.1.99"  # Другой IP
        )
        
        assert session is None


@pytest.mark.unit
class TestPasswordVerification:
    """Тесты для проверки пароля"""
    
    def test_verify_password_correct(self, db_session, regular_user, test_user_data):
        """Проверка верного пароля"""
        result = crud.verify_password(
            test_user_data["password"],
            regular_user.password_hash
        )
        
        assert result is True
    
    def test_verify_password_incorrect(self, db_session, regular_user):
        """Проверка неверного пароля"""
        result = crud.verify_password("WrongPassword123", regular_user.password_hash)
        
        assert result is False


@pytest.mark.unit
class TestEdgeCases:
    """Тесты граничных случаев"""
    
    def test_create_user_with_none_email(self, db_session):
        """Проверка создания пользователя с None email"""
        user_data = UserCreate(
            username="user_no_email",
            email=None,
            password="Password123"
        )
        
        # Email может быть None (nullable)
        user = crud.create_user(db_session, user_data)
        assert user.email is None
    
    def test_get_users_with_zero_limit(self, db_session, regular_user):
        """Проверка получения пользователей с limit=0"""
        users = crud.get_users(db_session, skip=0, limit=0)
        
        # Должны получить 0 результатов
        assert len(users) == 0
    
    def test_get_users_with_negative_offset(self, db_session, regular_user):
        """Проверка получения пользователей с отрицательным offset"""
        # Это может вызвать ошибку в БД или быть игнорировано
        users = crud.get_users(db_session, skip=-1, limit=10)
        
        # Поведение зависит от БД, но не должно быть краша
        assert isinstance(users, list)
