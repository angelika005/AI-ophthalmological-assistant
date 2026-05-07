import React, { useState } from 'react';
import { apiClient } from '../services/apiClient';

interface UploadedImage {
  id: number;
  original_url: string;
  processed_url: string;
  result: string;
  confidence: number;
  filename: string;
  created_at: string;
  status: string;
}

const ImageUpload: React.FC = () => {
  const [image, setImage] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<UploadedImage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      handleFileSelection(file);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelection(file);
    }
  };

  const handleFileSelection = (file: File) => {
    if (!file.type.startsWith('image/')) {
      setError('Пожалуйста, выберите изображение');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setError('Размер файла не должен превышать 10 МБ');
      return;
    }

    const imageUrl = URL.createObjectURL(file);
    setImage(imageUrl);
    setSelectedFile(file);
    setError(null);
    setUploadResult(null);
  };

  const uploadToServer = async () => {
    if (!selectedFile) {
      setError('Файл не выбран');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await apiClient.postFormData('/api/images/upload', formData);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Ошибка загрузки изображения');
      }

      const data: UploadedImage = await response.json();
      setUploadResult(data);
      // Заменяем локальный preview на реальный URL из MinIO
      setImage(data.original_url);
      console.log('Результат загрузки:', data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Неизвестная ошибка');
      console.error('Ошибка загрузки:', err);
    } finally {
      setUploading(false);
    }
  };

  const resetUpload = () => {
    setImage(null);
    setSelectedFile(null);
    setUploadResult(null);
    setError(null);
  };

  return (
    <div style={{ width: '100%', maxWidth: '600px', margin: '0 auto', padding: '20px' }}>
      {!image ? (
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          style={{
            border: dragActive ? '3px dashed #4a5feb' : '2px dashed #ccc',
            borderRadius: '12px',
            padding: '60px 20px',
            textAlign: 'center',
            cursor: 'pointer',
            backgroundColor: dragActive ? '#f0f4ff' : '#f9f9f9',
            transition: 'all 0.3s ease',
          }}
        >
          <p style={{ fontSize: '18px', color: '#666', marginBottom: '20px' }}>
            Перетащите сюда изображение<br />или кликните для выбора
          </p>
          <input
            id="file-upload"
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />
          <button
            onClick={() => document.getElementById('file-upload')?.click()}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#4a5feb';
              e.currentTarget.style.color = 'white';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
              e.currentTarget.style.color = '#4a5feb';
            }}
            style={{
              padding: '12px 30px',
              fontSize: '16px',
              border: '2px solid #4a5feb',
              borderRadius: '8px',
              backgroundColor: 'transparent',
              color: '#4a5feb',
              cursor: 'pointer',
              transition: 'all 0.3s ease',
            }}
          >
            Выбрать файл
          </button>
        </div>
      ) : (
        <div>
          <div style={{ textAlign: 'center', marginBottom: '20px' }}>
            <img
              src={image}
              alt="Preview"
              style={{
                maxWidth: '100%',
                maxHeight: '400px',
                borderRadius: '12px',
                boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
              }}
            />
          </div>

          {error && (
            <div
              style={{
                padding: '12px',
                marginBottom: '16px',
                backgroundColor: '#fee',
                color: '#c33',
                borderRadius: '8px',
                border: '1px solid #fcc',
              }}
            >
              {error}
            </div>
          )}

          {uploadResult && (
            <div
              style={{
                padding: '16px',
                marginBottom: '16px',
                backgroundColor: '#e8f5e9',
                borderRadius: '8px',
                border: '1px solid #4caf50',
              }}
            >
              <h3 style={{ margin: '0 0 12px 0', color: '#2e7d32' }}>Изображение загружено в MinIO!</h3>
              <p><strong>Статус:</strong> {uploadResult.result}</p>
              <p><strong>Вероятность:</strong> {(uploadResult.confidence * 100).toFixed(1)}%</p>
              <p><strong>Имя файла:</strong> {uploadResult.filename}</p>
            </div>
          )}

          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
            {!uploadResult && (
              <button
                onClick={uploadToServer}
                disabled={uploading}
                style={{
                  padding: '12px 30px',
                  fontSize: '16px',
                  border: 'none',
                  borderRadius: '8px',
                  backgroundColor: uploading ? '#ccc' : '#4a5feb',
                  color: 'white',
                  cursor: uploading ? 'not-allowed' : 'pointer',
                  transition: 'all 0.3s ease',
                }}
              >
                {uploading ? 'Загрузка в MinIO...' : 'Загрузить в MinIO'}
              </button>
            )}
            
            <button
              onClick={resetUpload}
              style={{
                padding: '12px 30px',
                fontSize: '16px',
                border: '2px solid #666',
                borderRadius: '8px',
                backgroundColor: 'transparent',
                color: '#666',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
              }}
            >
              {uploadResult ? 'Загрузить ещё' : 'Отменить'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ImageUpload;
