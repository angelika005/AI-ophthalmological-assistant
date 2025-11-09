import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import '../styles/Profile.css';

interface UserStats {
  total_checks: number;
  completed_checks: number;
  average_score: number;
}

interface Check {
  id: number;
  glaucoma_score: number;
  processing_time_ms: number;
  created_at: string;
}

interface UploadedImage {
  id: number;
  original_url: string;
  processed_url: string;
  result: string;
  glaucoma_probability: number;
  filename: string;
  file_size: number;
  status: string;
  created_at: string;
  processed_at: string | null;
}

const Profile: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState<UserStats | null>(null);
  const [checks, setChecks] = useState<Check[]>([]);
  const [loading, setLoading] = useState(true);
  const [images, setImages] = useState<UploadedImage[]>([]);
  const [loadingImages, setLoadingImages] = useState(false);
  const [deletingImageId, setDeletingImageId] = useState<number | null>(null);
  const [selectedImage, setSelectedImage] = useState<UploadedImage | null>(null);

  useEffect(() => {
    fetchUserStats();
    fetchUserChecks();
    fetchUserImages();
  }, []);

  const fetchUserStats = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/users/me/stats', {
        credentials: 'include',
      });
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Ошибка загрузки статистики:', error);
    }
  };

  const fetchUserChecks = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/users/me/checks', {
        credentials: 'include',
      });
      if (response.ok) {
        const data = await response.json();
        setChecks(data);
      }
    } catch (error) {
      console.error('Ошибка загрузки проверок:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchUserImages = async () => {
    setLoadingImages(true);
    try {
      const response = await fetch('http://localhost:8000/api/images', {
        credentials: 'include',
      });
      
      if (response.ok) {
        const data = await response.json();
        setImages(data);
      }
    } catch (error) {
      console.error('Ошибка загрузки изображений:', error);
    } finally {
      setLoadingImages(false);
    }
  };

  const deleteImage = async (imageId: number) => {
    if (!window.confirm('Удалить изображение из MinIO?')) return;
    
    setDeletingImageId(imageId);
    
    try {
      const response = await fetch(`http://localhost:8000/api/images/${imageId}`, {
        method: 'DELETE',
        credentials: 'include',
      });
      
      if (response.ok) {
        setImages(images.filter(img => img.id !== imageId));
        alert('✅ Изображение удалено из MinIO');
      } else {
        alert('❌ Ошибка удаления изображения');
      }
    } catch (error) {
      console.error('Ошибка удаления:', error);
      alert('❌ Ошибка удаления изображения');
    } finally {
      setDeletingImageId(null);
    }
  };

  const handleDeleteAccount = async () => {
    if (!window.confirm('Вы уверены, что хотите удалить свой аккаунт? Это действие необратимо.')) {
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/api/users/me', {
        method: 'DELETE',
        credentials: 'include',
      });

      if (response.ok) {
        logout();
        navigate('/');
      }
    } catch (error) {
      console.error('Ошибка удаления аккаунта:', error);
    }
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
            <h3>Завершено</h3>
            <p className="stat-value">{stats?.completed_checks || 0}</p>
          </div>
          <div className="stat-card">
            <h3>Средний балл</h3>
            <p className="stat-value">{stats?.average_score || 0}%</p>
          </div>
        </div>
      </div>

      <div className="profile-checks">
        <h2>История проверок</h2>
        {checks.length === 0 ? (
          <p>У вас пока нет сохранённых исследований</p>
        ) : (
          <div className="checks-list">
            {checks.map((check) => (
              <div key={check.id} className="check-card">
                <p><strong>Проверка #{check.id}</strong></p>
                <p>Балл глаукомы: {check.glaucoma_score}%</p>
                <p>Дата: {new Date(check.created_at).toLocaleString()}</p>
                {check.processing_time_ms && (
                  <p>Время обработки: {check.processing_time_ms}ms</p>
                )}
              </div>
            ))}
          </div>
        )}
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
                  Вероятность: {(image.glaucoma_probability * 100).toFixed(1)}%<br />
                  Размер: {(image.file_size / 1024).toFixed(1)} KB
                </p>
                
                <button 
                  onClick={() => deleteImage(image.id)}
                  disabled={deletingImageId === image.id}
                  className={`delete-image-button ${deletingImageId === image.id ? 'deleting' : ''}`}
                >
                  {deletingImageId === image.id ? '⏳ Удаление...' : '🗑️ Удалить'}
                </button>
              </div>
            ))}
          </div>
        )}
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
                Вероятность глаукомы: {(selectedImage.glaucoma_probability * 100).toFixed(1)}% | 
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
