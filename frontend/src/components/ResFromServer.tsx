import React, { useState, useEffect } from 'react';

const ResFromServer: React.FC = () => {
  const [text, setText] = useState<string>('Загрузка...');

  useEffect(() => {
    fetch('')
      .then(response => response.json())
      .then(data => {
        setText(data.title);
      })
      .catch(() => {
        setText('Ошибка загрузки данных');
      });
  }, []);

  return (
    <div style={{
    border: '2px dashed #d0d0d0',
    borderRadius: '16px',
    padding: '40px 32px',
    textAlign: 'center',
    width: '340px',
    minHeight: '280px',
    backgroundColor: '#ffffff',
    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.04)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    }}>
      <p style={{
        fontSize: '16px',
        color: '#4a4a4a',
        margin: 0,
        lineHeight: '1.5'
      }}>{text}</p>
    </div>
  );
}

export default ResFromServer;
