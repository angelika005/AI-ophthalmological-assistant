import React from 'react';
import ImageUpload from '../components/ImageUpLoad';

const WorkZone: React.FC = () => {
  return (
    <div style={{ padding: '80px 20px', maxWidth: '1200px', margin: '0 auto' }}>
      <h1 style={{ textAlign: 'center', marginBottom: '16px', color: '#333' }}>
        Загрузка изображений для анализа
      </h1>
      <p style={{ textAlign: 'center', color: '#666', marginBottom: '40px' }}>
        Загрузите изображение сетчатки глаза для обнаружения глаукомы. <br />
      </p>
      
      <ImageUpload />
    </div>
  );
};

export default WorkZone;
