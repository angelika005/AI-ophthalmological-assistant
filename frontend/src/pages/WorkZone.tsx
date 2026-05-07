import React from 'react';
import ImageUpload from '../components/ImageUpLoad';
import { useSEOMetaTags } from '../hooks/useSEOMetaTags';

const WorkZone: React.FC = () => {
  // ✅ SEO: защищённая страница - noindex
  useSEOMetaTags({
    title: 'Рабочая зона | AI Ophthalmological Assistant',
    description: 'Загрузите изображение сетчатки глаза для анализа на предмет глаукомы',
    canonical: window.location.origin + '/workzone',
    robotsDirective: 'noindex, follow'  // ✅ НЕ индексировать
  });

  return (
    <main style={{ padding: '80px 20px', maxWidth: '1200px', margin: '0 auto' }}>
      <h1 style={{ textAlign: 'center', marginBottom: '16px', color: '#333' }}>
        Загрузка изображений для анализа
      </h1>
      <p style={{ textAlign: 'center', color: '#666', marginBottom: '40px' }}>
        Загрузите изображение сетчатки глаза для обнаружения глаукомы. <br />
      </p>
      
      <ImageUpload />
    </main>
  );
};

export default WorkZone;
