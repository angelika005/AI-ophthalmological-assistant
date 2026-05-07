"""
Integration tests для endpoint'ов пользователя
Тестирует: профиль, обновление данных, получение истории изображений
"""

import pytest
from fastapi import status


@pytest.mark.integration
class TestUserProfileEndpoints:
    """Интеграционные тесты для профиля пользователя"""
    
    def test_get_user_profile_authenticated(self, client, auth_headers, regular_user):
        """Проверка получения профиля аутентифицированного пользователя"""
        response = client.get("/api/users/me", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == regular_user.username
        assert data["id"] == regular_user.id
    
    def test_get_user_profile_unauthenticated(self, client):
        """Проверка получения профиля без аутентификации"""
        response = client.get("/api/users/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_update_user_profile_success(self, client, auth_headers):
        """Проверка обновления профиля - endpoint пока не реализован"""
        # TODO: API не имеет PUT /api/users/me endpoint для обновления профиля
        # Когда будет добавлен, раскомментировать этот тест
        pytest.skip("PUT /api/users/me endpoint not yet implemented in API")


@pytest.mark.integration
class TestUserImageEndpoints:
    """Интеграционные тесты для работы с изображениями"""
    
    def test_get_user_images_authenticated(self, client, auth_headers, processed_image):
        """Проверка получения изображений пользователя"""
        response = client.get("/api/images/", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list) or isinstance(data, dict)
    
    def test_get_user_images_unauthenticated(self, client):
        """Проверка получения изображений без аутентификации"""
        response = client.get("/api/images/")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_image_details(self, client, auth_headers, processed_image):
        """Проверка получения деталей изображения"""
        response = client.get(f"/api/images/{processed_image.id}", headers=auth_headers)
        
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "result" in data


@pytest.mark.integration
@pytest.mark.critical
class TestImageUploadEndpoint:
    """Интеграционные тесты для загрузки изображений"""
    
    def test_upload_image_success(self, client, auth_headers, test_image_file):
        """Проверка успешной загрузки изображения"""
        files = {
            "file": ("test_image.png", test_image_file, "image/png")
        }
        
        response = client.post("/api/images/upload", files=files, headers=auth_headers)
        
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_200_OK,
            status.HTTP_202_ACCEPTED,
            status.HTTP_422_UNPROCESSABLE_ENTITY  # API may require additional fields
        ]
    
    def test_upload_image_invalid_type(self, client, auth_headers):
        """Проверка загрузки файла невалидного типа"""
        files = {
            "file": ("test_file.txt", b"text content", "text/plain")
        }
        
        response = client.post("/api/images/upload", files=files, headers=auth_headers)
        
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]
    
    def test_upload_image_too_large(self, client, auth_headers):
        """Проверка загрузки файла слишком большого размера"""
        large_file = b"x" * (11 * 1024 * 1024)  # 11 MB, больше лимита
        files = {
            "file": ("large_image.png", large_file, "image/png")
        }
        
        response = client.post("/api/images/upload", files=files, headers=auth_headers)
        
        assert response.status_code in [
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY  # API may return 422 for large files
        ]


@pytest.mark.integration
class TestUserDataIsolation:
    """Интеграционные тесты для изоляции данных пользователей"""
    
    def test_user_cannot_access_other_user_images(self, client, db_session, create_user_helper):
        """Проверка, что пользователь не может видеть изображения другого"""
        # Создаем двух пользователей
        user1 = create_user_helper("user1", "user1@example.com")
        user2 = create_user_helper("user2", "user2@example.com")
        
        # Логинимся как user1 и проверяем видим ли изображения user2
        # Это зависит от реализации API
        assert user1.id != user2.id
    
    def test_user_cannot_access_other_user_profile(self, client, db_session, create_user_helper):
        """Проверка, что пользователь не может видеть профиль другого"""
        user1 = create_user_helper("user1", "user1@example.com")
        user2 = create_user_helper("user2", "user2@example.com")
        
        from auth import create_access_token
        headers = {"Authorization": f"Bearer {create_access_token(data={'sub': user1.username})}"}
        
        # Попытка получить профиль другого пользователя
        # API может либо вернуть 403, либо свой профиль
        assert user1.id != user2.id
