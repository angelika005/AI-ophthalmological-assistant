import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { apiClient } from '../services/apiClient';
import '../styles/Profile.css';

interface UserStats {
  total_checks: number;
  glaucoma_count: number;
  non_glaucoma_count: number;
  today_uploads: number;
}

interface UploadedImage {
  id: number;
  original_url: string;
  processed_url: string;
  result: string;
  confidence: number;
  filename: string;
  file_size: number;
  status: string;
  created_at: string;
  processed_at: string | null;
}

const Profile: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [stats, setStats] = useState<UserStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [images, setImages] = useState<UploadedImage[]>([]);
  const [totalImages, setTotalImages] = useState(0);
  const [loadingImages, setLoadingImages] = useState(false);
  const [deletingImageId, setDeletingImageId] = useState<number | null>(null);
  const [selectedImage, setSelectedImage] = useState<UploadedImage | null>(null);

  const page = Math.max(Number(searchParams.get('page') || '1'), 1);
  const pageSize = Math.max(Number(searchParams.get('page_size') || '12'), 1);
  const search = searchParams.get('search') || '';
  const status = searchParams.get('status') || '';
  const result = searchParams.get('result') || '';
  const sortBy = searchParams.get('sort_by') || 'created_at';
  const sortOrder = searchParams.get('sort_order') || 'desc';
  const totalPages = Math.max(Math.ceil(totalImages / pageSize), 1);

  const fetchUserStats = useCallback(async () => {
    try {
      const response = await apiClient.get('/api/users/me/stats');
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Ошибка загрузки статистики:', error);
    }
  }, []);

  const fetchUserImages = useCallback(async () => {
    setLoadingImages(true);
    try {
      const params = new URLSearchParams(searchParams);
      if (!params.get('page')) params.set('page', '1');
      if (!params.get('page_size')) params.set('page_size', '12');
      const response = await apiClient.get(`/api/images?${params.toString()}`);
      
      if (response.ok) {
        const data = await response.json();
        if (Array.isArray(data)) {
          setImages(data);
          setTotalImages(data.length);
        } else {
          setImages(data.items || []);
          setTotalImages(data.total || 0);
        }
      }
    } catch (error) {
      console.error('Ошибка загрузки изображений:', error);
    } finally {
      setLoadingImages(false);
      setLoading(false);
    }
  }, [searchParams]);

  useEffect(() => {
    fetchUserStats();
  }, [fetchUserStats]);

  useEffect(() => {
    fetchUserImages();
  }, [fetchUserImages]);

  const deleteImage = async (imageId: number) => {
    if (!window.confirm('Удалить изображение из MinIO?')) return;
    
    setDeletingImageId(imageId);
    
    try {
      const response = await apiClient.delete(`/api/images/${imageId}`);
      
      if (response.ok) {
        setImages(images.filter(img => img.id !== imageId));
        alert('Изображение удалено из MinIO');
      } else {
        alert('Ошибка удаления изображения');
      }
    } catch (error) {
      console.error('Ошибка удаления:', error);
      alert('Ошибка удаления изображения');
    } finally {
      setDeletingImageId(null);
    }
  };

  const handleDeleteAccount = async () => {
    if (!window.confirm('Вы уверены, что хотите удалить свой аккаунт? Это действие необратимо.')) {
      return;
    }

    try {
      const response = await apiClient.delete('/api/users/me');

      if (response.ok) {
        logout();
        navigate('/');
      }
    } catch (error) {
      console.error('Ошибка удаления аккаунта:', error);
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
    return <div className="profile-container">Загрузка профиля...</div>;
  }

  const handleBackToWorkZone = () => {
    navigate('/workzone');
  };

  return (
    <div className="profile-container">
      <div className="profWorkZoneButton">
        <div className="profName">
          <h1>Профиль пользователя</h1>
        </div>
        <div className="header-buttons"> 
          {user?.role === 'admin' && (
            <button 
              onClick={() => navigate('/admin')} 
              className="admin-btn"
              title="Перейти в администраторскую панель"
            >
              Админ-панель
            </button>
          )}
          <button onClick={handleBackToWorkZone} className="back-btn">
            ← Рабочая зона
          </button>
        </div>
      </div>
      <div className="profile-info">
        <h2>Информация о пользователе</h2>
        <p><strong>Имя пользователя:</strong> {user?.username || '-'}</p>
        <p><strong>Email:</strong> {user?.email || 'Не указан'}</p>
        <p><strong>ID:</strong> {user?.id || '-'}</p>
      </div>

      <div className="profile-stats">
        <h2>Статистика</h2>
        <div className="stats-grid">
          <div className="stat-card">
            <h3>Всего проверок</h3>
            <p className="stat-value">{stats?.total_checks || 0}</p>
          </div>
          <div className="stat-card">
            <h3>С глаукомой</h3>
            <p className="stat-value">{stats?.glaucoma_count || 0}</p>
          </div>
          <div className="stat-card">
            <h3>Без глаукомы</h3>
            <p className="stat-value">{stats?.non_glaucoma_count || 0}</p>
          </div>
          <div className="stat-card">
            <h3>Загрузок сегодня</h3>
            <p className="stat-value">{stats?.today_uploads || 0}</p>
          </div>
        </div>
      </div>

      <div className="images-section">
        <div className="images-header">
          <h2>Мои изображения в MinIO</h2>
          <button 
            onClick={fetchUserImages}
            disabled={loadingImages}
            className={`refresh-button ${loadingImages ? 'loading' : ''}`}
          >
            {loadingImages ? '⏳ Загрузка...' : 'Обновить список'}
          </button>
        </div>

        <div className="profile-image-filters">
          <input
            className="profile-filter-input"
            placeholder="Поиск по имени файла/результату"
            value={search}
            onChange={(e) => updateParam('search', e.target.value, true)}
          />
          <select
            className="profile-filter-select"
            value={status}
            onChange={(e) => updateParam('status', e.target.value, true)}
          >
            <option value="">Любой статус</option>
            <option value="pending">pending</option>
            <option value="processing">processing</option>
            <option value="completed">completed</option>
            <option value="failed">failed</option>
          </select>
          <select
            className="profile-filter-select"
            value={result}
            onChange={(e) => updateParam('result', e.target.value, true)}
          >
            <option value="">Любой результат</option>
            <option value="glaucoma">glaucoma</option>
            <option value="non-glaucoma">non-glaucoma</option>
          </select>
          <select
            className="profile-filter-select"
            value={sortBy}
            onChange={(e) => updateParam('sort_by', e.target.value, true)}
          >
            <option value="created_at">Сортировка: дата</option>
            <option value="filename">Сортировка: имя</option>
            <option value="file_size">Сортировка: размер</option>
            <option value="status">Сортировка: статус</option>
          </select>
          <select
            className="profile-filter-select"
            value={sortOrder}
            onChange={(e) => updateParam('sort_order', e.target.value, true)}
          >
            <option value="desc">DESC</option>
            <option value="asc">ASC</option>
          </select>
          <select
            className="profile-filter-select"
            value={String(pageSize)}
            onChange={(e) => updateParam('page_size', e.target.value, true)}
          >
            <option value="12">12 / page</option>
            <option value="24">24 / page</option>
            <option value="50">50 / page</option>
          </select>
        </div>
        
        {loadingImages ? (
          <p>Загрузка...</p>
        ) : images.length === 0 ? (
          <p className="no-images">Изображений пока нет. Загрузите первое в VisionX!</p>
        ) : (
          <div className="images-grid">
            {images.map(image => (
              <div key={image.id} className="image-card">
                <img 
                  src={image.original_url} 
                  alt={image.filename}
                  onClick={() => setSelectedImage(image)}
                  onError={(e) => {
                    const target = e.currentTarget;
                    target.src = 'https://via.placeholder.com/250x150?text=Image+Not+Found';
                    target.classList.add('error');
                  }}
                  className="image-thumbnail"
                />
                <p className="image-filename">{image.filename}</p>
                <p className="image-details">
                  Статус: {image.result}<br />
                  Вероятность: {(image.confidence * 100).toFixed(1)}%<br />
                  Размер: {(image.file_size / 1024).toFixed(1)} KB
                </p>
                
                <button 
                  onClick={() => deleteImage(image.id)}
                  disabled={deletingImageId === image.id}
                  className={`delete-image-button ${deletingImageId === image.id ? 'deleting' : ''}`}
                >
                  {deletingImageId === image.id ? 'Удаление...' : 'Удалить'}
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="profile-pagination">
          <button onClick={() => goToPage(page - 1)} disabled={page <= 1} className="refresh-button">
            Prev
          </button>
          <span>Страница {page} из {totalPages}</span>
          <button onClick={() => goToPage(page + 1)} disabled={page >= totalPages} className="refresh-button">
            Next
          </button>
        </div>
      </div>

      {selectedImage && (
        <div className="modal-overlay" onClick={() => setSelectedImage(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <img 
              src={selectedImage.original_url} 
              alt={selectedImage.filename}
              className="modal-image"
            />
            
            <div className="modal-info">
              <p className="modal-filename">{selectedImage.filename}</p>
              <p className="modal-details">
                Вероятность: {(selectedImage.confidence * 100).toFixed(1)}% | 
                Размер: {(selectedImage.file_size / 1024).toFixed(1)} KB
              </p>
            </div>

            <button
              onClick={() => setSelectedImage(null)}
              className="modal-close-button"
            >
              ✕ Закрыть
            </button>
          </div>
        </div>
      )}

      <div className="profile-actions">
        <button onClick={handleDeleteAccount} className="delete-button">
          Удалить аккаунт
        </button>
      </div>
    </div>
  );
};

export default Profile;
