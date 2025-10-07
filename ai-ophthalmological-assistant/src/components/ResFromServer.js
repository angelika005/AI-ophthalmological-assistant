import React, { useState, useEffect } from 'react';

function ResFromServer() {
  const [text, setText] = useState('Загрузка...');

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
    padding: '10px',
    border: '2px dashed #ccc',
    borderRadius: '10px',
    marginTop: '20px',
    padding: '20px',
    textAlign: 'center',
    width: '300px',
    height: '200px',
    backgroundColor: '#f3fdff',
    }}>
      <p>{text}</p>
    </div>
  );
}

export default ResFromServer;