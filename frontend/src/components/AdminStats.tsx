import React, { useState, useEffect } from 'react';
import { apiClient } from '../services/apiClient';

interface SystemStats {
  total_users: number;
  active_users: number;
  blocked_users: number;
  admin_count: number;
  user_count: number;
}

const AdminStats: React.FC = () => {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const handleRefresh = async () => {
    await fetchStats();
  };

  const fetchStats = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get('/api/admin/stats');

      if (!response.ok) {
        throw new Error('Ошибка загрузки статистики');
      }

      const data = await response.json();
      setStats(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Неизвестная ошибка');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="admin-section">Загрузка статистики...</div>;
  }

  if (error) {
    return (
      <div className="admin-section">
        <div className="error-message">{error}</div>
        <button onClick={fetchStats} className="retry-btn">
          Повторить
        </button>
      </div>
    );
  }

  if (!stats) {
    return <div className="admin-section">Данные недоступны</div>;
  }

  const adminPercentage = stats.total_users > 0 
    ? Math.round((stats.admin_count / stats.total_users) * 100) 
    : 0;
  
  const activePercentage = stats.total_users > 0 
    ? Math.round((stats.active_users / stats.total_users) * 100) 
    : 0;

  return (
    <div className="admin-section">
      <div className="section-header">
        <h2>Статистика системы</h2>
        <button 
          onClick={handleRefresh} 
          className="refresh-btn" 
          disabled={loading}
          title="Обновить статистику"
        >
          {loading ? 'Обновление...' : 'Обновить'}
        </button>
      </div>

      <div className="stats-grid">
        <div className="stat-card primary">
          <h3>Total Users</h3>
          <div className="stat-number">{stats.total_users}</div>
          <p className="stat-label">всего пользователей</p>
        </div>

        <div className="stat-card success">
          <h3>Active Users</h3>
          <div className="stat-number">{stats.active_users}</div>
          <p className="stat-label">{activePercentage}% активных</p>
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${activePercentage}%` }}
            />
          </div>
        </div>

        <div className="stat-card danger">
          <h3>Blocked Users</h3>
          <div className="stat-number">{stats.blocked_users}</div>
          <p className="stat-label">заблокировано</p>
        </div>

        <div className="stat-card warning">
          <h3>Administrators</h3>
          <div className="stat-number">{stats.admin_count}</div>
          <p className="stat-label">{adminPercentage}% администраторов</p>
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${adminPercentage}%` }}
            />
          </div>
        </div>

        <div className="stat-card info">
          <h3>Regular Users</h3>
          <div className="stat-number">{stats.user_count}</div>
          <p className="stat-label">врачей в системе</p>
        </div>

        <div className="stat-card">
          <h3>System Health</h3>
          <div className="health-indicator">
            {stats.total_users > 0 && stats.active_users > stats.total_users * 0.8 ?
              <>
                <div className="health-badge good">Good</div>
                <p>Система работает нормально</p>
              </>
              : stats.total_users > 0 && stats.active_users > stats.total_users * 0.5 ?
              <>
                <div className="health-badge warning">Warning</div>
                <p>Есть заблокированные пользователи</p>
              </>
              :
              <>
                <div className="health-badge error">Critical</div>
                <p>Проверьте активные учетные записи</p>
              </>
            }
          </div>
        </div>
      </div>

      <div className="stats-details">
        <h3>Детальная информация</h3>
        <div className="details-grid">
          <div className="detail-item">
            <label>Активных пользователей:</label>
            <span className="value success">{stats.active_users} / {stats.total_users}</span>
          </div>
          <div className="detail-item">
            <label>Заблокировано:</label>
            <span className="value danger">{stats.blocked_users}</span>
          </div>
          <div className="detail-item">
            <label>Администраторов:</label>
            <span className="value warning">{stats.admin_count}</span>
          </div>
          <div className="detail-item">
            <label>Обычных пользователей (врачей):</label>
            <span className="value info">{stats.user_count}</span>
          </div>
        </div>
      </div>

      <div className="chart-container">
        <h3>Распределение по ролям</h3>
        <div className="pie-chart">
          <div className="pie-slice admin" style={{ transform: `rotate(0deg) skewY(${16 * (stats.admin_count / stats.total_users)}deg)` }}>
            <span className="label">Admin ({stats.admin_count})</span>
          </div>
          <div className="pie-slice user" style={{ transform: `rotate(${360 * (stats.admin_count / stats.total_users)}deg)` }}>
            <span className="label">User ({stats.user_count})</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminStats;
