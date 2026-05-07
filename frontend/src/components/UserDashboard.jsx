import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import '../index';

const UserDashboard = () => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    fetchHistory();
  }, [user]);

  const fetchHistory = async () => {
    if (!user) return;

    try {
      const response = await fetch(`http://localhost:8000/api/user/${user.id}/history`, {
        headers: {
          'Authorization': `Bearer ${user.token}`,
        },
      });
      const data = await response.json();
      setHistory(data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching history:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Загрузка...</div>;
  }

  return (
    <div className="dashboard">
      <h1>История запросов</h1>
      <div className="history-list">
        {history.length === 0 ? (
          <p>История пуста</p>
        ) : (
          history.map((item) => (
            <div key={item.id} className="history-item">
              <div className="image-container">
                <img 
                  src={item.imageUrl} 
                  alt="Результат анализа" 
                  className="result-image"
                />
              </div>
              <div className="result-container">
                <h3>Результат модели:</h3>
                <p>{item.modelResult}</p>
                <span className="timestamp">
                  {new Date(item.createdAt).toLocaleString('ru-RU')}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default UserDashboard;
