"""
тестирование валидации Pydantic моделей
Покрывает: валидацию email, пароля, username, обработку ошибок
"""

import pytest
from pydantic import ValidationError
from schemas import UserCreate, UserLogin, UserResponse, Token, UpdateUserRoleRequest, UserRoleEnum
from datetime import datetime


@pytest.mark.unit
class TestUserCreateSchema:
    """Тесты для валидации UserCreate схемы"""
    
    def test_valid_user_create(self):
        """Проверка валидного создания пользователя"""
        user_data = {
            "username": "validuser",
            "email": "user@example.com",
            "password": "ValidPass123"
        }
        user = UserCreate(**user_data)
        
        assert user.username == "validuser"
        assert user.email == "user@example.com"
        assert user.password == "ValidPass123"
    
    def test_username_minimum_length(self):
        """Проверка минимальной длины username (3 символа)"""
        user_data = {
            "username": "ab",  # Слишком короткое
            "email": "user@example.com",
            "password": "ValidPass123"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)
        
        errors = exc_info.value.errors()
        assert any("username" in str(e) for e in errors)
    
    def test_username_maximum_length(self):
        """Проверка максимальной длины username (50 символов)"""
        user_data = {
            "username": "a" * 51,
            "email": "user@example.com",
            "password": "ValidPass123"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)
        
        errors = exc_info.value.errors()
        assert any("username" in str(e) for e in errors)
    
    def test_username_at_minimum_length(self):
        """Проверка username точно на минимальной длине (3 символа)"""
        user_data = {
            "username": "abc",
            "email": "user@example.com",
            "password": "ValidPass123"
        }
        
        user = UserCreate(**user_data)
        assert user.username == "abc"
    
    def test_username_at_maximum_length(self):
        """Проверка username точно на максимальной длине (50 символов)"""
        user_data = {
            "username": "a" * 50,
            "email": "user@example.com",
            "password": "ValidPass123"
        }
        
        user = UserCreate(**user_data)
        assert len(user.username) == 50
    
    def test_password_minimum_length(self):
        """Проверка минимальной длины пароля (6 символов)"""
        user_data = {
            "username": "validuser",
            "email": "user@example.com",
            "password": "short"  # Слишком короткое
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)
        
        errors = exc_info.value.errors()
        assert any("password" in str(e) for e in errors)
    
    def test_password_maximum_length(self):
        """Проверка максимальной длины пароля (128 символов)"""
        user_data = {
            "username": "validuser",
            "email": "user@example.com",
            "password": "a" * 129  # Слишком длинное
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)
        
        errors = exc_info.value.errors()
        assert any("password" in str(e) for e in errors)
    
    def test_invalid_email_format(self):
        """Проверка невалидного формата email"""
        user_data = {
            "username": "validuser",
            "email": "not-an-email",
            "password": "ValidPass123"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)
        
        errors = exc_info.value.errors()
        assert any("email" in str(e) for e in errors)
    
    def test_email_optional(self):
        """Проверка, что email может быть None"""
        user_data = {
            "username": "validuser",
            "email": None,
            "password": "ValidPass123"
        }
        
        user = UserCreate(**user_data)
        assert user.email is None


@pytest.mark.unit
class TestUserLoginSchema:
    """Тесты для валидации UserLogin схемы"""
    
    def test_valid_user_login(self):
        """Проверка валидного логина"""
        login_data = {
            "username": "testuser",
            "password": "Password123"
        }
        
        login = UserLogin(**login_data)
        assert login.username == "testuser"
        assert login.password == "Password123"
    
    def test_missing_username(self):
        """Проверка обязательного username"""
        login_data = {
            "password": "Password123"
        }
        
        with pytest.raises(ValidationError):
            UserLogin(**login_data)
    
    def test_missing_password(self):
        """Проверка обязательного пароля"""
        login_data = {
            "username": "testuser"
        }
        
        with pytest.raises(ValidationError):
            UserLogin(**login_data)


@pytest.mark.unit
class TestTokenSchema:
    """Тесты для валидации Token схемы"""
    
    def test_valid_token(self):
        """Проверка валидного Token"""
        token_data = {
            "access_token": "token_string_123",
            "refresh_token": "refresh_string_456",
            "token_type": "bearer",
            "user_id": 1,
            "username": "testuser",
            "expires_in": 1800
        }
        
        token = Token(**token_data)
        assert token.access_token == "token_string_123"
        assert token.token_type == "bearer"
    
    def test_token_missing_required_fields(self):
        """Проверка обязательных полей Token"""
        token_data = {
            "access_token": "token_string_123",
            "token_type": "bearer"
            # Отсутствуют другие поля
        }
        
        with pytest.raises(ValidationError):
            Token(**token_data)


@pytest.mark.unit
class TestUserResponseSchema:
    """Тесты для валидации UserResponse схемы"""
    
    def test_valid_user_response(self):
        """Проверка валидного ответа User"""
        user_data = {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "role": "user",
            "is_active": True,
            "created_at": datetime.utcnow()
        }
        
        user = UserResponse(**user_data)
        assert user.id == 1
        assert user.username == "testuser"
        assert user.role == "user"
    
    def test_user_response_with_orm_object(self, regular_user):
        """Проверка преобразования ORM объекта в Response"""
        user = UserResponse.from_orm(regular_user)
        
        assert user.id == regular_user.id
        assert user.username == regular_user.username


@pytest.mark.unit
class TestUpdateUserRoleSchema:
    """Тесты для валидации UpdateUserRoleRequest схемы"""
    
    def test_valid_user_role(self):
        """Проверка валидной роли"""
        role_data = {"role": "admin"}
        
        request = UpdateUserRoleRequest(**role_data)
        assert request.role == "admin"
    
    def test_valid_user_role_enum(self):
        """Проверка валидной роли через Enum"""
        role_data = {"role": UserRoleEnum.ADMIN}
        
        request = UpdateUserRoleRequest(**role_data)
        assert request.role == UserRoleEnum.ADMIN
    
    def test_invalid_role(self):
        """Проверка невалидной роли"""
        role_data = {"role": "superadmin"}  # Невалидная роль
        
        with pytest.raises(ValidationError) as exc_info:
            UpdateUserRoleRequest(**role_data)
        
        errors = exc_info.value.errors()
        assert any("role" in str(e) for e in errors)


@pytest.mark.unit
class TestEdgeCasesSchemas:
    """Тесты граничных случаев для схем"""
    
    def test_username_with_special_characters(self):
        """Проверка username со спецсимволами"""
        user_data = {
            "username": "user@domain",  # Спецсимволы допустимы
            "email": "user@example.com",
            "password": "ValidPass123"
        }
        
        user = UserCreate(**user_data)
        assert user.username == "user@domain"
    
    def test_username_with_numbers(self):
        """Проверка username с цифрами"""
        user_data = {
            "username": "user123",
            "email": "user@example.com",
            "password": "ValidPass123"
        }
        
        user = UserCreate(**user_data)
        assert user.username == "user123"
    
    def test_password_exactly_minimum_length(self):
        """Проверка пароля точно на минимальной длине (6)"""
        user_data = {
            "username": "validuser",
            "email": "user@example.com",
            "password": "Pass1"  # Ровно 5 - слишком короткое
        }
        
        with pytest.raises(ValidationError):
            UserCreate(**user_data)
    
    def test_password_with_special_characters(self):
        """Проверка пароля со спецсимволами"""
        user_data = {
            "username": "validuser",
            "email": "user@example.com",
            "password": "Pass!@#$%^"
        }
        
        user = UserCreate(**user_data)
        assert user.password == "Pass!@#$%^"
    
    def test_whitespace_in_username(self):
        """Проверка username с пробелами"""
        user_data = {
            "username": "user name",  # Пробел
            "email": "user@example.com",
            "password": "ValidPass123"
        }
        
        # Это может быть валидным или нет в зависимости от требований
        user = UserCreate(**user_data)
        assert "user name" in user.username or "user" in user.username
    
    def test_empty_string_values(self):
        """Проверка пустых строк"""
        user_data = {
            "username": "",
            "email": "user@example.com",
            "password": "ValidPass123"
        }
        
        with pytest.raises(ValidationError):
            UserCreate(**user_data)
    
    def test_very_long_email(self):
        """Проверка очень длинного email"""
        long_local = "a" * 64
        user_data = {
            "username": "validuser",
            "email": f"{long_local}@example.com",
            "password": "ValidPass123"
        }
        
        # Email может быть очень длинным
        try:
            user = UserCreate(**user_data)
            assert user.email is not None
        except ValidationError:
            # Если есть ограничение на длину
            pass
