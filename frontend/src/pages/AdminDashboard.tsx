import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import '../styles/AdminDashboard.css';
import AdminUsersList from '../components/AdminUsersList';
import AdminStats from '../components/AdminStats';

type AdminTab = 'users' | 'stats' | 'info';

const AdminDashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<AdminTab>('stats');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }

    // Проверка прав администратора
    if (user.role !== 'admin') {
      navigate('/workzone');
      return;
    }

    setLoading(false);
  }, [user, navigate]);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  if (loading) {
    return <div className="admin-container">Загрузка...</div>;
  }

  if (!user || user.role !== 'admin') {
    return <div className="admin-container">Доступ запрещен</div>;
  }

  return (
    <div className="admin-container">
      <div className="admin-header">
        <div className="admin-title">
          <h1>🔐 Администраторская панель</h1>
          <p>Управление системой и пользователями</p>
        </div>
        <div className="admin-user-info">
          <span>Вход как: <strong>{user.username}</strong> (Admin)</span>
          <button onClick={handleLogout} className="logout-btn">
            Выход
          </button>
          <button 
            onClick={() => navigate('/profile')} 
            className="back-btn"
          >
            ← Профиль
          </button>
        </div>
      </div>

      <div className="admin-tabs">
        <button
          className={`tab-btn ${activeTab === 'stats' ? 'active' : ''}`}
          onClick={() => setActiveTab('stats')}
        >
          Статистика
        </button>
        <button
          className={`tab-btn ${activeTab === 'users' ? 'active' : ''}`}
          onClick={() => setActiveTab('users')}
        >
          Пользователи
        </button>
        <button
          className={`tab-btn ${activeTab === 'info' ? 'active' : ''}`}
          onClick={() => setActiveTab('info')}
        >
          Информация
        </button>
      </div>

      <div className="admin-content">
        {activeTab === 'stats' && <AdminStats />}
        {activeTab === 'users' && <AdminUsersList />}
        {activeTab === 'info' && <AdminInfo />}
      </div>
    </div>
  );
};

const AdminInfo: React.FC = () => {
  return (
    <div className="admin-info-panel">
      <h2>Информация о системе</h2>
      
      <div className="info-grid">
        <div className="info-card">
          <h3>Назначение</h3>
          <p>AI Ophthalmological Assistant - система для диагностики глаукомы с использованием распределяемых нейронных сетей.</p>
        </div>

        <div className="info-card">
          <h3>Технологический стек</h3>
          <ul>
            <li><strong>Backend:</strong> FastAPI + Python</li>
            <li><strong>Frontend:</strong> React + TypeScript</li>
            <li><strong>БД:</strong> PostgreSQL 15</li>
            <li><strong>Storage:</strong> MinIO (S3-compatible)</li>
            <li><strong>ML Model:</strong> SwinV2-Tiny (HuggingFace)</li>
          </ul>
        </div>

        <div className="info-card">
          <h3>Безопасность</h3>
          <ul>
            <li>JWT Authentication (Access + Refresh tokens)</li>
            <li>Argon2 Password Hashing</li>
            <li>Role-Based Access Control (RBAC)</li>
            <li>CORS Protection</li>
            <li>Cookie-based sessions</li>
          </ul>
        </div>

        <div className="info-card">
          <h3>Роли пользователей</h3>
          <ul>
            <li><strong>USER (Врач):</strong> Загрузка и анализ изображений, личная статистика</li>
            <li><strong>ADMIN:</strong> Управление всеми пользователями, полный доступ к данным</li>
          </ul>
        </div>

        <div className="info-card">
          <h3>Основные функции</h3>
          <ul>
            <li>Загрузка фотографий сетчатки глаза</li>
            <li>Автоматический анализ ML-моделью</li>
            <li>Результаты с уровнем уверенности (confidence)</li>
            <li>История проверок и статистика</li>
            <li>Управление пользователями (админ)</li>
          </ul>
        </div>

        <div className="info-card">
          <h3>API версия</h3>
          <p><strong>v1.0.0</strong></p>
          <p>API Documentation: <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer">Swagger UI</a></p>
        </div>
      </div>

      <div className="admin-guide">
        <h2>Руководство администратора</h2>
        
        <div className="guide-section">
          <h3>1. Управление пользователями</h3>
          <p>На вкладке "Пользователи" вы можете:</p>
          <ul>
            <li>Просмотреть всех пользователей системы</li>
            <li>Изменить роль пользователя (user ↔ admin)</li>
            <li>Заблокировать/разблокировать пользователей</li>
            <li>Удалить пользователя (необратимо)</li>
          </ul>
        </div>

        <div className="guide-section">
          <h3>2. Просмотр статистики</h3>
          <p>На вкладке "Статистика" отображается:</p>
          <ul>
            <li>Общее количество пользователей подсистемы</li>
            <li>Количество активных/заблокированных</li>
            <li>Распределение по ролям (админов/врачей)</li>
          </ul>
        </div>

        <div className="guide-section">
          <h3>3. Меры безопасности</h3>
          <ul>
            <li>Все действия администратора логируются в backend</li>
            <li>Админ не может изменить свою роль (защита)</li>
            <li>Админ не может заблокировать себя</li>
            <li>Пароли хранятся в виде хешей Argon2</li>
          </ul>
        </div>

        <div className="guide-section">
          <h3>4. Полезные команды (Terminal)</h3>
          <code className="code-block">
            # Сделать пользователя администратором<br/>
            docker exec -it glaucoma_db psql -U postgres -d glaucoma_db -c "UPDATE users SET role = 'admin' WHERE username = 'username';"<br/>
            <br/>
            # Заблокировать пользователя<br/>
            docker exec -it glaucoma_db psql -U postgres -d glaucoma_db -c "UPDATE users SET is_active = false WHERE username = 'username';"<br/>
            <br/>
            # Просмотр всех пользователей<br/>
            docker exec -it glaucoma_db psql -U postgres -d glaucoma_db -c "SELECT id, username, role, is_active FROM users;"
          </code>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
