import React, { useState } from 'react';

function ImageUpload() {
  const [image, setImage] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
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
        border: dragActive ? '2px dashed #06f' : '2px dashed #ccc',
        borderRadius: '10px',
        marginTop: '40px',
        padding: '20px',
        textAlign: 'center',
        cursor: 'pointer',
        width: '300px',
        height: '200px',
        backgroundColor: '#f3fdff',
      }}
    >
      <p>Перетащите сюда изображение или кликните для выбора</p>
      {image && <img src={image} alt="Загруженное" style={{ maxWidth: '100%', marginTop: 10 }} />}
      <input
        type="file"
        accept="image/*"
        onChange={(e) => {
          const file = e.target.files[0];
          if (file) {
            const imageUrl = URL.createObjectURL(file);
            setImage(imageUrl);
          }
        }}
        style={{ display: 'none' }}
        id="fileUpload"
      />
      <label htmlFor="fileUpload" style={{ cursor: 'pointer', color: '#06f', textDecoration: 'underline' }}>
        Выбрать файл
      </label>
    </div>
  );
}

export default ImageUpload;