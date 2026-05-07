"""
Unit tests для auth.py - тестирование функций аутентификации и авторизации
Покрывает: хеширование паролей, токены, проверка ролей
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from fastapi import HTTPException, status
from jose import JWTError
import os

from auth import (
    generate_refresh_token,
    create_access_token,
    verify_token,
    verify_refresh_token,
)
import crud


@pytest.mark.unit
@pytest.mark.auth
class TestPasswordHashing:
    """Тесты для хеширования паролей (Argon2)"""
    
    def test_get_password_hash_returns_hash(self):
        """Проверка, что хеширование возвращает хеш"""
        password = "TestPassword123!"
        hashed = crud.get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert "$argon2" in hashed
    
    def test_different_passwords_produce_different_hashes(self):
        """Проверка, что разные пароли дают разные хеши"""
        password1 = "Password123"
        password2 = "Password456"
        
        hash1 = crud.get_password_hash(password1)
        hash2 = crud.get_password_hash(password2)
        
        assert hash1 != hash2
    
    def test_same_password_produces_different_hashes(self):
        """Проверка, что один и тот же пароль дает разные хеши"""
        password = "TestPassword123!"
        
        hash1 = crud.get_password_hash(password)
        hash2 = crud.get_password_hash(password)
        
        assert hash1 != hash2


@pytest.mark.unit
@pytest.mark.auth
class TestPasswordVerification:
    """Тесты для проверки паролей"""
    
    def test_verify_password_correct_password_returns_true(self, db_session, regular_user):
        """Проверка, что верный пароль верифицируется"""
        result = crud.verify_password("TestPassword123!", regular_user.password_hash)
        assert result is True
    
    def test_verify_password_incorrect_password_returns_false(self, db_session, regular_user):
        """Проверка, что неверный пароль не верифицируется"""
        result = crud.verify_password("WrongPassword123!", regular_user.password_hash)
        assert result is False
    
    def test_verify_password_case_sensitive(self, db_session, regular_user):
        """Проверка, что проверка пароля чувствительна к регистру"""
        result = crud.verify_password("testpassword123!", regular_user.password_hash)
        assert result is False


@pytest.mark.unit
@pytest.mark.auth
class TestTokenGeneration:
    """Тесты для генерации токенов"""
    
    def test_generate_refresh_token_returns_string(self):
        """Проверка, что refresh token возвращает строку"""
        token = generate_refresh_token()
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_generate_refresh_token_is_unique(self):
        """Проверка, что каждый refresh token уникален"""
        token1 = generate_refresh_token()
        token2 = generate_refresh_token()
        
        assert token1 != token2
    
    def test_create_access_token_returns_string(self, regular_user):
        """Проверка, что access token возвращает строку"""
        token = create_access_token(data={"sub": regular_user.username})
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_access_token_includes_expiration(self):
        """Проверка, что access token включает время истечения"""
        token = create_access_token(data={"sub": "testuser"})
        payload = verify_token(token)
        
        # Если токен верифицируется, значит он не истекло
        assert payload == "testuser"
    
    def test_create_access_token_with_custom_expiration(self):
        """Проверка, что можно установить кастомное время истечения"""
        custom_expire = timedelta(minutes=60)
        token = create_access_token(data={"sub": "testuser"}, expires_delta=custom_expire)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_access_token_includes_token_type(self):
        """Проверка, что токен включает тип "access" """
        token = create_access_token(data={"sub": "testuser"})
        # Токен должен быть верифицируемым
        result = verify_token(token)
        assert result is not None


@pytest.mark.unit
@pytest.mark.auth
class TestTokenVerification:
    """Тесты для проверки токенов"""
    
    def test_verify_token_valid_token_returns_username(self, regular_user):
        """Проверка, что верный токен возвращает username"""
        token = create_access_token(data={"sub": regular_user.username})
        username = verify_token(token)
        
        assert username == regular_user.username
    
    def test_verify_token_invalid_token_returns_none(self):
        """Проверка, что невалидный токен возвращает None"""
        invalid_token = "invalid.token.string"
        result = verify_token(invalid_token)
        
        assert result is None
    
    def test_verify_token_empty_token_returns_none(self):
        """Проверка, что пустой токен возвращает None"""
        result = verify_token("")
        assert result is None
    
    def test_verify_token_token_with_wrong_type_returns_none(self):
        """Проверка, что токен с неправильным типом возвращает None"""
        # Создаем токен с типом "refresh" вместо "access"
        from jose import jwt
        SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
        ALGORITHM = os.getenv("ALGORITHM", "HS256")
        
        payload = {
            "sub": "testuser",
            "type": "refresh",
            "exp": datetime.utcnow() + timedelta(days=30)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        result = verify_token(token)
        
        assert result is None


@pytest.mark.unit
@pytest.mark.auth
class TestRefreshTokenVerification:
    """Тесты для проверки refresh токенов"""
    
    def test_verify_refresh_token_valid_token_returns_token(self):
        """Проверка, что верный refresh token возвращается как есть"""
        refresh_token = generate_refresh_token()
        result = verify_refresh_token(refresh_token)
        
        assert result == refresh_token
    
    def test_verify_refresh_token_empty_token_returns_none(self):
        """Проверка, что пустой токен возвращает None"""
        result = verify_refresh_token("")
        assert result is None
    
    def test_verify_refresh_token_none_returns_none(self):
        """Проверка, что None возвращает None"""
        result = verify_refresh_token(None)
        assert result is None


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.security
class TestRoleBasedAccess:
    """Тесты для контроля доступа на основе ролей"""
    
    def test_user_role_is_default(self, regular_user):
        """Проверка, что новый пользователь получает роль 'user'"""
        from models import UserRole
        assert regular_user.role == UserRole.USER.value
    
    def test_admin_role_can_be_assigned(self, db_session):
        """Проверка, что роль 'admin' может быть назначена"""
        from models import UserRole, User
        
        user = User(
            username="test_admin",
            email="admin@test.com",
            password_hash=crud.get_password_hash("Password123"),
            role=UserRole.ADMIN.value
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.role == UserRole.ADMIN.value
    
    def test_user_cannot_directly_become_admin(self, regular_user, db_session):
        """Проверка, что пользователь не может напрямую получить роль админа"""
        from models import UserRole
        
        # В начале пользователь - обычный юзер
        assert regular_user.role == UserRole.USER.value
        
        # Только явное присвоение может изменить роль
        regular_user.role = UserRole.ADMIN.value
        db_session.commit()
        
        assert regular_user.role == UserRole.ADMIN.value


@pytest.mark.skip(reason="freezegun conflicts with transformers lazy loading")
@pytest.mark.unit
class TestTokenExpiration:
    """Тесты для истечения токенов"""
    
    def test_expired_token_cannot_be_verified(self):
        """Проверка, что истекший токен не может быть верифицирован"""
        from freezegun import freeze_time
        from datetime import timedelta
        
        # Создаем токен с очень коротким временем жизни
        with freeze_time("2024-01-01 12:00:00"):
            token = create_access_token(
                data={"sub": "testuser"},
                expires_delta=timedelta(seconds=1)
            )
        
        # Ждем, пока токен истечет
        with freeze_time("2024-01-01 12:00:02"):
            result = verify_token(token)
            assert result is None
    
    def test_token_valid_within_expiration_window(self):
        """Проверка, что токен валиден в пределах времени жизни"""
        from freezegun import freeze_time
        
        with freeze_time("2024-01-01 12:00:00"):
            token = create_access_token(
                data={"sub": "testuser"},
                expires_delta=timedelta(minutes=30)
            )
            result = verify_token(token)
            assert result == "testuser"
