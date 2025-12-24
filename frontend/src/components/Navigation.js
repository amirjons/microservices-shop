import React from 'react';

// Компонент навигационной панели
export const Navigation = ({ activeTab, setActiveTab }) => (
  <nav className="app-nav">
    <div className="nav-content">
      {/* Массив конфигурации вкладок. Мы проходимся по нему map-ом, чтобы создать кнопки */}
      {[
        { id: 'account', label: '💰 Счет' },
        { id: 'orders', label: '📦 Заказы' },
        { id: 'dashboard', label: '📊 Статистика' }
      ].map(tab => (
        <button
          key={tab.id}
          // Обработчик клика: устанавливаем id выбранной вкладки как активный
          onClick={() => setActiveTab(tab.id)}
          // Динамический класс: если id вкладки совпадает с активным, добавляем стиль 'active'
          className={`nav-tab ${activeTab === tab.id ? 'active' : ''}`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  </nav>
);