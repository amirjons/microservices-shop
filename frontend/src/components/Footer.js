import React from 'react';

// Компонент "Подвал" страницы с полезными ссылками и контактами
export const Footer = ({ apiUrl }) => (
  <footer className="app-footer">
    <div className="footer-content">

      {/* Левая секция с названием бренда */}
      <div className="footer-left">
        <div className="footer-brand">Г ozон</div>
      </div>

      <div className="footer-links">
        {/* Ссылка на документацию API (Swagger) */}
        <a href={`${apiUrl}/docs`} target="_blank" rel="noopener noreferrer">
          <i className="fas fa-book mr-1"></i> Swagger
        </a>
        {/* Ссылка на панель управления очередями сообщений (RabbitMQ) */}
        <a href="http://localhost:15672" target="_blank" rel="noopener noreferrer">
          <i className="fas fa-layer-group mr-1"></i> RabbitMQ
        </a>
      </div>

      {/* Правая секция с контактами разработчика */}
      <div className="footer-contacts" style={{display: 'flex', gap: '1rem'}}>
        <a href="https://t.me/ammiirrjon" target="_blank" rel="noopener noreferrer" className="contact-link" style={{color: '#667eea', textDecoration: 'none', fontWeight: 600}}>
          <i className="fab fa-telegram text-xl"></i> @ammiirrjon
        </a>
        <a href="mailto:a6403610@gmail.com" className="contact-link" style={{color: '#667eea', textDecoration: 'none', fontWeight: 600}}>
          <i className="fas fa-envelope text-xl"></i> a6403610@gmail.com
        </a>
      </div>
    </div>

    {/* Нижняя полоса с копирайтом */}
    <div className="footer-copyright">
      <p>© 2025 Интернет-магазин "Г ozон". Все права защищены.</p>
    </div>
  </footer>
);