import React, { useState } from 'react';

interface ImageUploadProps {}

const ImageUpload: React.FC<ImageUploadProps> = () => {
  const [image, setImage] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState<boolean>(false);

  const handleDrag = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      const imageUrl = URL.createObjectURL(file);
      setImage(imageUrl);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const imageUrl = URL.createObjectURL(file);
      setImage(imageUrl);
    }
  };

  return (
    <div
      onDragEnter={handleDrag}
      onDragOver={handleDrag}
      onDragLeave={handleDrag}
      onDrop={handleDrop}
      style={{
        border: dragActive ? '2px solid #4a5feb' : '2px dashed #d0d0d0',
        borderRadius: '16px',
        padding: '40px 32px',
        textAlign: 'center',
        cursor: 'pointer',
        width: '340px',
        minHeight: '280px',
        backgroundColor: '#ffffff',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.04)',
        transition: 'all 0.2s ease',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      {!image ? (
        <>
          <p style={{ 
            fontSize: '16px', 
            color: '#4a4a4a', 
            margin: '0 0 16px 0',
            lineHeight: '1.5'
          }}>
            Перетащите сюда изображение<br/>или кликните для выбора
          </p>
          <label 
            htmlFor="fileUpload" 
            style={{ 
              cursor: 'pointer', 
              color: '#4a5feb', 
              fontSize: '15px',
              fontWeight: '600',
              padding: '10px 24px',
              border: '1px solid #4a5feb',
              borderRadius: '8px',
              transition: 'all 0.2s ease',
              display: 'inline-block'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#4a5feb';
              e.currentTarget.style.color = 'white';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
              e.currentTarget.style.color = '#4a5feb';
            }}
          >
            Выбрать файл
          </label>
        </>
      ) : (
        <img 
          src={image} 
          alt="Загруженное" 
          style={{ 
            maxWidth: '100%', 
            maxHeight: '240px',
            borderRadius: '8px',
            objectFit: 'contain'
          }} 
        />
      )}
      <input
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        style={{ display: 'none' }}
        id="fileUpload"
      />
    </div>
  );
}

export default ImageUpload;
