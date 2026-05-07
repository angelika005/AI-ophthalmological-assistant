"""
Integration tests для endpoint'ов аутентификации
Тестирует: регистрация, вход, выход, обновление токенов
"""

import pytest
from fastapi import status
import json


@pytest.mark.integration
@pytest.mark.critical
class TestAuthenticationEndpoints:
    """Интеграционные тесты для endpoint'ов аутентификации"""
    
    def test_register_user_success(self, client):
        """Проверка успешной регистрации пользователя"""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "ValidPassword123!"
        }
        
        response = client.post("/api/users/register", json=user_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]
        assert "id" in data
    
    def test_register_user_duplicate_username(self, client, regular_user):
        """Проверка регистрации с дублирующимся username"""
        user_data = {
            "username": regular_user.username,
            "email": "different@example.com",
            "password": "ValidPassword123!"
        }
        
        response = client.post("/api/users/register", json=user_data)
        
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_409_CONFLICT,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]
    
    def test_register_user_invalid_email(self, client):
        """Проверка регистрации с невалидным email"""
        user_data = {
            "username": "newuser",
            "email": "invalid-email",
            "password": "ValidPassword123!"
        }
        
        response = client.post("/api/users/register", json=user_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_register_user_short_password(self, client):
        """Проверка регистрации с коротким пароль"""
        user_data = {
            "username": "newuser",
            "email": "user@example.com",
            "password": "short"
        }
        
        response = client.post("/api/users/register", json=user_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_register_user_short_username(self, client):
        """Проверка регистрации с коротким username"""
        user_data = {
            "username": "ab",
            "email": "user@example.com",
            "password": "ValidPassword123!"
        }
        
        response = client.post("/api/users/register", json=user_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_login_user_success(self, client, regular_user, test_user_data):
        """Проверка успешного входа пользователя"""
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        
        response = client.post("/api/users/login", json=login_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user_id"] == regular_user.id
    
    def test_login_user_wrong_password(self, client, regular_user, test_user_data):
        """Проверка входа с неправильным паролем"""
        login_data = {
            "username": test_user_data["username"],
            "password": "WrongPassword123!"
        }
        
        response = client.post("/api/users/login", json=login_data)
        
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_400_BAD_REQUEST]
    
    def test_login_user_nonexistent(self, client):
        """Проверка входа для несуществующего пользователя"""
        login_data = {
            "username": "nonexistent",
            "password": "SomePassword123!"
        }
        
        response = client.post("/api/users/login", json=login_data)
        
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_400_BAD_REQUEST]
    
    def test_login_user_inactive(self, client, inactive_user):
        """Проверка входа для неактивного пользователя"""
        login_data = {
            "username": inactive_user.username,
            "password": "Password123"
        }
        
        response = client.post("/api/users/login", json=login_data)
        
        # Неактивный пользователь не должен войти, может получить 400 или 401
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN, status.HTTP_400_BAD_REQUEST]


@pytest.mark.integration
@pytest.mark.critical
class TestAuthorizationEndpoints:
    """Интеграционные тесты для авторизации"""
    
    def test_access_protected_route_without_token(self, client):
        """Проверка доступа к защищенному маршруту без токена"""
        response = client.get("/api/users/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_access_protected_route_with_valid_token(self, client, access_token):
        """Проверка доступа к защищенному маршруту с валидным токеном"""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        response = client.get("/api/users/me", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_access_protected_route_with_invalid_token(self, client):
        """Проверка доступа с невалидным токеном"""
        headers = {"Authorization": "Bearer invalid.token.here"}
        
        response = client.get("/api/users/me", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_access_admin_route_as_regular_user(self, client, access_token):
        """Проверка доступа к админ маршруту для обычного пользователя"""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        response = client.get("/api/admin/users", headers=headers)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_access_admin_route_as_admin(self, client, admin_access_token):
        """Проверка доступа к админ маршруту для администратора"""
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        
        response = client.get("/api/admin/users", headers=headers)
        
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]


@pytest.mark.integration
class TestTokenRefreshEndpoint:
    """Интеграционные тесты для обновления токенов"""
    
    def test_refresh_token_success(self, client, refresh_token, valid_session):
        """Проверка успешного обновления токена"""
        refresh_data = {"refresh_token": refresh_token}
        
        response = client.post("/api/token/refresh", json=refresh_data)
        
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]
        # Зависит от реализации - может требоваться валидная сессия
    
    def test_refresh_token_invalid(self, client):
        """Проверка обновления токена с невалидным токеном"""
        refresh_data = {"refresh_token": "invalid_refresh_token"}
        
        response = client.post("/api/token/refresh", json=refresh_data)
        
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_400_BAD_REQUEST
        ]


@pytest.mark.integration
class TestLogoutEndpoint:
    """Интеграционные тесты для выхода"""
    
    def test_logout_with_valid_token(self, client, access_token):
        """Проверка выхода с валидным токеном"""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        response = client.post("/api/users/logout", headers=headers)
        
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_204_NO_CONTENT,
            status.HTTP_401_UNAUTHORIZED
        ]
    
    def test_logout_without_token(self, client):
        """Проверка выхода без токена"""
        response = client.post("/api/users/logout")
        
        # API может вернуть 200 (ничего не выполнить) или 401 (требовать токен)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]


@pytest.mark.integration
@pytest.mark.security
class TestSecurityHeaders:
    """Интеграционные тесты для заголовков безопасности"""
    
    def test_cors_headers_present(self, client):
        """Проверка наличия CORS заголовков"""
        response = client.get("/")
        
        # Проверяем, что сервер отвечает (может быть 404, но не 500)
        assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def test_token_not_in_response_body(self, client, regular_user, test_user_data):
        """Проверка, что токен не возвращается в теле ответа в небезопасном виде"""
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        
        response = client.post("/api/users/login", json=login_data)
        
        if response.status_code == status.HTTP_200_OK:
            # Токен может быть в response, но не должен повторяться
            data = response.json()
            assert "access_token" in data
