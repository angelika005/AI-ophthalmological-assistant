import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { apiClient } from '../services/apiClient';
import { useSearchParams } from 'react-router-dom';

interface User {
  id: number;
  username: string;
  email: string;
  role: 'user' | 'admin';
  is_active: boolean;
  created_at: string;
}

interface UsersResponse {
  items: User[];
  total: number;
  page: number;
  page_size: number;
}

const AdminUsersList: React.FC = () => {
  const { user: currentUser } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [users, setUsers] = useState<User[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<number | null>(null);

  const page = Math.max(Number(searchParams.get('page') || '1'), 1);
  const pageSize = Math.max(Number(searchParams.get('page_size') || '10'), 1);
  const search = searchParams.get('search') || '';
  const role = searchParams.get('role') || '';
  const status = searchParams.get('is_active') || '';
  const sortBy = searchParams.get('sort_by') || 'created_at';
  const sortOrder = searchParams.get('sort_order') || 'desc';

  const totalPages = Math.max(Math.ceil(total / pageSize), 1);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams(searchParams);
      const response = await apiClient.get(`/api/admin/users?${params.toString()}`);

      if (!response.ok) {
        throw new Error(`Failed to fetch users: ${response.statusText}`);
      }

      const data: UsersResponse = await response.json();
      setUsers(data.items || []);
      setTotal(data.total || 0);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка загрузки пользователей');
    } finally {
      setLoading(false);
    }
  }, [searchParams]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const updateUserRole = async (userId: number, newRole: 'user' | 'admin') => {
    if (userId === currentUser?.id) {
      setError('Вы не можете изменить свою роль');
      return;
    }

    setUpdatingId(userId);
    try {
      const response = await apiClient.patch(
        `/api/admin/users/${userId}/role`,
        { role: newRole }
      );

      if (!response.ok) {
        throw new Error('Ошибка при изменении роли');
      }

      // Обновляем список пользователей
      await fetchUsers();
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Неизвестная ошибка');
    } finally {
      setUpdatingId(null);
    }
  };

  const updateUserStatus = async (userId: number, isActive: boolean) => {
    if (userId === currentUser?.id) {
      setError('Вы не можете изменить свой статус');
      return;
    }

    setUpdatingId(userId);
    try {
      const response = await apiClient.patch(
        `/api/admin/users/${userId}/status`,
        { is_active: isActive }
      );

      if (!response.ok) {
        const data = await response.json().catch(() => null);
        throw new Error(data?.detail || 'Ошибка изменения статуса');
      }

      await fetchUsers();
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Неизвестная ошибка');
    } finally {
      setUpdatingId(null);
    }
  };

  const deleteUser = async (userId: number) => {
    if (userId === currentUser?.id) {
      setError('Вы не можете удалить себя');
      return;
    }

    if (!window.confirm('Удалить пользователя? Действие необратимо.')) {
      return;
    }

    setUpdatingId(userId);
    try {
      const response = await apiClient.delete(`/api/admin/users/${userId}`);
      if (!response.ok) {
        const data = await response.json().catch(() => null);
        throw new Error(data?.detail || 'Ошибка удаления пользователя');
      }

      await fetchUsers();
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Неизвестная ошибка');
    } finally {
      setUpdatingId(null);
    }
  };

  const editUser = async (target: User) => {
    const username = window.prompt('Новый username (минимум 3 символа):', target.username)?.trim();
    const email = window.prompt('Новый email (или оставьте пустым):', target.email || '')?.trim();

    if (!username) {
      return;
    }

    if (username.length < 3) {
      setError('Username должен содержать минимум 3 символа');
      return;
    }

    if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError('Некорректный email');
      return;
    }

    setUpdatingId(target.id);
    try {
      const response = await apiClient.put(`/api/admin/users/${target.id}`, {
        username,
        email: email || null,
      });

      if (!response.ok) {
        const data = await response.json().catch(() => null);
        throw new Error(data?.detail || 'Ошибка обновления профиля');
      }

      await fetchUsers();
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Неизвестная ошибка');
    } finally {
      setUpdatingId(null);
    }
  };

  const updateParam = (key: string, value: string, resetPage = false) => {
    const next = new URLSearchParams(searchParams);
    if (value) {
      next.set(key, value);
    } else {
      next.delete(key);
    }
    if (resetPage) {
      next.set('page', '1');
    }
    setSearchParams(next);
  };

  const goToPage = (nextPage: number) => {
    const safePage = Math.min(Math.max(nextPage, 1), totalPages);
    updateParam('page', String(safePage));
  };

  if (loading) {
    return <div className="admin-section">📥 Загрузка пользователей...</div>;
  }

  return (
    <div className="admin-section">
      <div className="section-header">
        <h2>Управление пользователями</h2>
        <button onClick={fetchUsers} className="refresh-btn">
          Обновить
        </button>
      </div>

      <div className="users-filters">
        <input
          type="text"
          value={search}
          onChange={(e) => updateParam('search', e.target.value, true)}
          placeholder="Поиск по username/email"
          className="filter-input"
        />

        <select
          value={role}
          onChange={(e) => updateParam('role', e.target.value, true)}
          className="filter-select"
        >
          <option value="">Все роли</option>
          <option value="user">User</option>
          <option value="admin">Admin</option>
        </select>

        <select
          value={status}
          onChange={(e) => updateParam('is_active', e.target.value, true)}
          className="filter-select"
        >
          <option value="">Любой статус</option>
          <option value="true">Active</option>
          <option value="false">Blocked</option>
        </select>

        <select
          value={sortBy}
          onChange={(e) => updateParam('sort_by', e.target.value, true)}
          className="filter-select"
        >
          <option value="created_at">Сортировка: дата</option>
          <option value="username">Сортировка: username</option>
          <option value="email">Сортировка: email</option>
          <option value="role">Сортировка: role</option>
          <option value="is_active">Сортировка: status</option>
        </select>

        <select
          value={sortOrder}
          onChange={(e) => updateParam('sort_order', e.target.value, true)}
          className="filter-select"
        >
          <option value="desc">DESC</option>
          <option value="asc">ASC</option>
        </select>

        <select
          value={String(pageSize)}
          onChange={(e) => updateParam('page_size', e.target.value, true)}
          className="filter-select"
        >
          <option value="10">10 / page</option>
          <option value="20">20 / page</option>
          <option value="50">50 / page</option>
        </select>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="users-table-wrapper">
        <table className="users-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Username</th>
              <th>Email</th>
              <th>Роль</th>
              <th>Статус</th>
              <th>Дата регистрации</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className={!u.is_active ? 'disabled-user' : ''}>
                <td><strong>#{u.id}</strong></td>
                <td>{u.username}</td>
                <td>{u.email || '—'}</td>
                <td>
                  <span className={`role-badge ${u.role}`}>
                    {u.role === 'admin' ? 'Admin' : 'User'}
                  </span>
                </td>
                <td>
                  <span className={`status-badge ${u.is_active ? 'active' : 'blocked'}`}>
                    {u.is_active ? 'Active' : 'Blocked'}
                  </span>
                </td>
                <td className="date-cell">{new Date(u.created_at).toLocaleDateString()}</td>
                <td className="actions-cell">
                  {u.id !== currentUser?.id && (
                    <div className="actions-group">
                      <button
                        onClick={() =>
                          updateUserRole(u.id, u.role === 'admin' ? 'user' : 'admin')
                        }
                        disabled={updatingId === u.id}
                        className={`action-btn ${u.role === 'admin' ? 'revoke' : 'promote'}`}
                      >
                        {updatingId === u.id ? '...' : u.role === 'admin' ? 'Revoke' : 'Promote'}
                      </button>

                      <button
                        onClick={() => updateUserStatus(u.id, !u.is_active)}
                        disabled={updatingId === u.id}
                        className={`action-btn ${u.is_active ? 'revoke' : 'promote'}`}
                      >
                        {updatingId === u.id ? '...' : u.is_active ? 'Block' : 'Unblock'}
                      </button>

                      <button
                        onClick={() => editUser(u)}
                        disabled={updatingId === u.id}
                        className="action-btn promote"
                      >
                        Edit
                      </button>

                      <button
                        onClick={() => deleteUser(u.id)}
                        disabled={updatingId === u.id}
                        className="action-btn revoke"
                      >
                        Delete
                      </button>
                    </div>
                  )}
                  {u.id === currentUser?.id && (
                    <span className="self-indicator">Это вы</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="users-summary">
        <p>
          <strong>Total users:</strong> {total} | 
          <strong> Admins:</strong> {users.filter(u => u.role === 'admin').length} | 
          <strong> Active:</strong> {users.filter(u => u.is_active).length}
        </p>
      </div>

      <div className="pagination-controls">
        <button onClick={() => goToPage(page - 1)} disabled={page <= 1} className="refresh-btn">
          Prev
        </button>
        <span>
          Page {page} of {totalPages}
        </span>
        <button onClick={() => goToPage(page + 1)} disabled={page >= totalPages} className="refresh-btn">
          Next
        </button>
      </div>
    </div>
  );
};

export default AdminUsersList;
