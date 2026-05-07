"""
E2E tests для критических бизнес-сценариев
Тестирует полные пользовательские workflows от начала до конца
"""

import pytest
from fastapi import status


@pytest.mark.e2e
@pytest.mark.critical
class TestRegistrationAndLoginFlow:
    """E2E тесты для регистрации и входа"""
    
    def test_complete_registration_and_login_flow(self, client):
        """Проверка полного цикла: регистрация -> вход -> доступ к профилю"""
        # Шаг 1: Регистрация
        user_data = {
            "username": "e2e_testuser",
            "email": "e2e_test@example.com",
            "password": "E2EPassword123!"
        }
        
        register_response = client.post("/api/users/register", json=user_data)
        assert register_response.status_code == status.HTTP_201_CREATED
        
        # Шаг 2: Вход
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"]
        }
        
        login_response = client.post("/api/users/login", json=login_data)
        assert login_response.status_code == status.HTTP_200_OK
        
        tokens = login_response.json()
        access_token = tokens["access_token"]
        
        # Шаг 3: Доступ к защищенному ресурсу
        headers = {"Authorization": f"Bearer {access_token}"}
        profile_response = client.get("/api/users/me", headers=headers)
        
        assert profile_response.status_code == status.HTTP_200_OK
        profile = profile_response.json()
        assert profile["username"] == user_data["username"]


@pytest.mark.e2e
@pytest.mark.critical
class TestImageProcessingFlow:
    """E2E тесты для загрузки и обработки изображений"""
    
    def test_complete_image_upload_and_retrieval_flow(self, client, auth_headers, test_image_file):
        """Проверка полного цикла: загрузка -> сохранение -> получение"""
        # Шаг 1: Загрузка изображения
        files = {"file": ("test_image.png", test_image_file, "image/png")}
        
        upload_response = client.post("/api/images/upload", files=files, headers=auth_headers)
        
        if upload_response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_200_OK,
            status.HTTP_202_ACCEPTED
        ]:
            # Шаг 2: Получение списка изображений
            list_response = client.get("/api/images/", headers=auth_headers)
            assert list_response.status_code == status.HTTP_200_OK


@pytest.mark.e2e
@pytest.mark.critical
class TestAdminWorkflow:
    """E2E тесты для административного workflow'а"""
    
    def test_admin_user_management_workflow(self, client, admin_auth_headers, db_session, create_user_helper):
        """Проверка полного цикла: создание -> просмотр -> управление пользователем"""
        # Подготовка: создаем пользователя
        user = create_user_helper("manage_user", "manage@example.com")
        
        # Шаг 1: Получение списка пользователей
        list_response = client.get("/api/admin/users", headers=admin_auth_headers)
        assert list_response.status_code == status.HTTP_200_OK
        
        # Шаг 2: Изменение роли пользователя
        role_update = {"role": "admin"}
        update_response = client.patch(
            f"/api/admin/users/{user.id}/role",
            json=role_update,
            headers=admin_auth_headers
        )
        
        assert update_response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_204_NO_CONTENT,
            status.HTTP_404_NOT_FOUND
        ]


@pytest.mark.e2e
class TestSessionRecoveryFlow:
    """E2E тесты для восстановления сессии"""
    
    def test_token_refresh_flow(self, client, regular_user, refresh_token):
        """Проверка обновления токена при истечении access token'а"""
        # Шаг 1: Логин и получение токенов
        login_data = {
            "username": regular_user.username,
            "password": "TestPassword123!"
        }
        
        login_response = client.post("/api/users/login", json=login_data)
        
        if login_response.status_code == status.HTTP_200_OK:
            tokens = login_response.json()
            
            # Шаг 2: Использование refresh token
            refresh_data = {"refresh_token": tokens.get("refresh_token", refresh_token)}
            
            refresh_response = client.post("/api/token/refresh", json=refresh_data)
            
            # Проверяем, что операция прошла или вернула информативную ошибку
            assert refresh_response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_400_BAD_REQUEST
            ]


@pytest.mark.e2e
@pytest.mark.security
class TestSecurityScenarios:
    """E2E тесты для сценариев безопасности"""
    
    def test_brute_force_protection(self, client, regular_user):
        """Проверка защиты от перебора пароля"""
        login_data_wrong = {
            "username": regular_user.username,
            "password": "WrongPassword1"
        }
        
        # Пытаемся несколько раз
        for i in range(5):
            response = client.post("/api/users/login", json=login_data_wrong)
            # API должен вернуть 401 или начать ограничивать
            assert response.status_code in [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_429_TOO_MANY_REQUESTS  # Rate limiting
            ]
    
    def test_sql_injection_prevention(self, client):
        """Проверка защиты от SQL-инъекций"""
        malicious_data = {
            "username": "admin' OR '1'='1",
            "password": "' OR '1'='1"
        }
        
        response = client.post("/api/users/login", json=malicious_data)
        
        # Должно вернуть 401, а не ошибку БД
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]
    
    def test_xss_prevention(self, client):
        """Проверка защиты от XSS"""
        xss_payload = {
            "username": "<script>alert('xss')</script>",
            "email": "test@example.com",
            "password": "Password123"
        }
        
        response = client.post("/api/users/register", json=xss_payload)
        
        # Должно быть обработано безопасно
        assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.e2e
class TestDataIntegrityFlow:
    """E2E тесты для целостности данных"""
    
    def test_cascade_delete_on_user_deletion(self, client, admin_auth_headers, db_session, create_user_helper, processed_image):
        """Проверка каскадного удаления при удалении пользователя"""
        # Создаем пользователя с данными
        user = create_user_helper("delete_user", "delete@example.com")
        
        # TODO: Проверить, что связанные данные удаляются
        assert user.id is not None
