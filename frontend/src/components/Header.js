import React from 'react';

// Компонент "Шапка" страницы, содержащий логотип, переключатель темы,
// поле ввода User ID, статус WebSocket и кнопку обновления данных.
export const Header = ({ userId, setUserId, wsConnected, darkMode, setDarkMode, onRefresh }) => (
  <header className="app-header">
    <div className="header-content">

      {/* Левая секция: Логотип и название приложения */}
      <div className="header-left">
        <div className="logo-container">
          <div className="logo-icon">🛍️</div>
          <div className="logo-text">
            <h1 className="logo-title">Интернет-магазин "Г ozон"</h1>
            <p className="logo-subtitle">Панель управления</p>
          </div>
        </div>
      </div>

      {/* Правая секция: Элементы управления и статусы */}
      <div className="header-right">

        {/* Кнопка переключения темной/светлой темы */}
        <button
          onClick={() => setDarkMode(!darkMode)}
          className="theme-toggle"
          aria-label="Переключить тему"
        >
          {darkMode ? '☀️' : '🌙'}
        </button>

        {/* Поле для ввода идентификатора пользователя (User ID) */}
        <div className="user-id-input">
          <span>ID пользователя:</span>
          <input
            type="number"
            value={userId}
            onChange={(e) => setUserId(parseInt(e.target.value) || 1)}
            min="1"
          />
        </div>

        {/* Индикатор статуса WebSocket соединения */}
        <div className={`ws-status ${wsConnected ? 'connected' : 'disconnected'}`}>
          <div className="ws-indicator"></div>
          <span>{wsConnected ? 'Онлайн' : 'Оффлайн'}</span>
        </div>

        {/* Кнопка ручного обновления всех данных */}
        <button onClick={onRefresh} className="btn-refresh"><span>🔄 Обновить</span></button>
      </div>
    </div>
  </header>
);