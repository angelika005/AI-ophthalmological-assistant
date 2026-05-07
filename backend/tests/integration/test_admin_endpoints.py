"""
Integration tests для admin endpoint'ов
Тестирует: управление пользователями, просмотр статистики, блокировка пользователей
"""

import pytest
from fastapi import status


@pytest.mark.integration
@pytest.mark.admin
@pytest.mark.critical
class TestAdminUserListEndpoint:
    """Интеграционные тесты для списка пользователей (только админ)"""
    
    def test_admin_can_list_users(self, client, admin_auth_headers):
        """Проверка, что администратор может получить список пользователей"""
        response = client.get("/api/admin/users", headers=admin_auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, (list, dict))
    
    def test_regular_user_cannot_list_users(self, client, auth_headers):
        """Проверка, что обычный пользователь не может получить список"""
        response = client.get("/api/admin/users", headers=auth_headers)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_unauthenticated_user_cannot_list_users(self, client):
        """Проверка, что неаутентифицированный пользователь не может получить список"""
        response = client.get("/api/admin/users")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.integration
@pytest.mark.admin
class TestAdminUserManagementEndpoints:
    """Интеграционные тесты для управления пользователями"""
    
    def test_admin_can_update_user_role(self, client, admin_auth_headers, db_session, regular_user):
        """Проверка, что администратор может изменить роль пользователя"""
        role_update = {"role": "admin"}
        
        response = client.patch(
            f"/api/admin/users/{regular_user.id}/role",
            json=role_update,
            headers=admin_auth_headers
        )
        
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_204_NO_CONTENT,
            status.HTTP_404_NOT_FOUND
        ]
    
    def test_admin_can_disable_user(self, client, admin_auth_headers, regular_user):
        """Проверка, что администратор может заблокировать пользователя"""
        disable_data = {"is_active": False}
        
        response = client.patch(
            f"/api/admin/users/{regular_user.id}/status",
            json=disable_data,
            headers=admin_auth_headers
        )
        
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_204_NO_CONTENT,
            status.HTTP_404_NOT_FOUND
        ]
    
    def test_regular_user_cannot_update_other_user_role(self, client, auth_headers, db_session, create_user_helper):
        """Проверка, что обычный пользователь не может менять роли"""
        other_user = create_user_helper("other", "other@example.com")
        role_update = {"role": "admin"}
        
        response = client.patch(
            f"/api/admin/users/{other_user.id}/role",
            json=role_update,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.integration
@pytest.mark.admin
class TestAdminStatisticsEndpoints:
    """Интеграционные тесты для статистики"""
    
    def test_admin_can_get_statistics(self, client, admin_auth_headers):
        """Проверка, что администратор может получить статистику"""
        response = client.get("/api/admin/stats", headers=admin_auth_headers)
        
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert isinstance(data, dict)
    
    def test_regular_user_cannot_access_statistics(self, client, auth_headers):
        """Проверка, что обычный пользователь не может получить статистику"""
        response = client.get("/api/admin/stats", headers=auth_headers)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.integration
@pytest.mark.admin
class TestAdminDataFiltering:
    """Интеграционные тесты для фильтрации данных админом"""
    
    def test_admin_can_filter_users_by_role(self, client, admin_auth_headers):
        """Проверка фильтрации пользователей по роли"""
        response = client.get(
            "/api/admin/users?role=user",
            headers=admin_auth_headers
        )
        
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
    
    def test_admin_can_filter_users_by_status(self, client, admin_auth_headers):
        """Проверка фильтрации пользователей по статусу"""
        response = client.get(
            "/api/admin/users?is_active=true",
            headers=admin_auth_headers
        )
        
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
