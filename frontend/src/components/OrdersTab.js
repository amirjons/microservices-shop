import React, { useState } from 'react';

// Вспомогательная функция для определения цвета статуса заказа
// Возвращает CSS-класс в зависимости от статуса (FINISHED, CANCELLED, NEW)
const getStatusColor = (status) => {
  switch (status) {
    case 'FINISHED': return 'status-finished';
    case 'CANCELLED': return 'status-cancelled';
    default: return 'status-new';
  }
};

// Компонент вкладки "Заказы"
// orders: список заказов для отображения
// onCreate: функция-обработчик для создания нового заказа
export const OrdersTab = ({ orders, onCreate }) => {
  // Локальное состояние формы
  const [form, setForm] = useState({ amount: '', description: '' });

  // Обработчик отправки формы
  const handleSubmit = () => {
    // Проверка на пустое поле суммы
    if (!form.amount) return;

    // Вызываем функцию создания заказа, преобразуя сумму в число
    onCreate({ ...form, amount: parseFloat(form.amount) });

    // Очищаем поля формы после отправки
    setForm({ amount: '', description: '' });
  };

  return (
    <div className="tab-content fade-in">

      {/* Карточка формы создания заказа */}
      <div className="card">
        <h2 className="card-title">Создать новый заказ</h2>
        <div className="order-form">

          {/* Поле ввода суммы */}
          <div className="input-group">
            <label>Сумма заказа (₽)</label>
            <input
              type="number"
              value={form.amount}
              onChange={e => setForm({...form, amount: e.target.value})}
              placeholder="Введите стоимость"
            />
          </div>

          {/* Поле ввода описания */}
          <div className="input-group">
            <label>Описание товара</label>
            <input
              type="text"
              value={form.description}
              onChange={e => setForm({...form, description: e.target.value})}
              placeholder="Например: Ноутбук"
            />
          </div>
        </div>

        {/* Кнопка отправки */}
        <button onClick={handleSubmit} className="btn-primary">
          Оформить заказ
        </button>
      </div>

      {/* Карточка списка истории заказов */}
      <div className="card orders-card">
        <h2 className="card-title">История заказов</h2>
        <div className="orders-table-container">
          <table className="orders-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Сумма</th>
                <th>Описание</th>
                <th>Статус</th>
              </tr>
            </thead>
            <tbody>
              {/* Рендеринг строк таблицы заказов */}
              {orders.map(o => (
                <tr key={o.id} className="order-row">
                  <td>#{o.id}</td>
                  <td>{o.amount} ₽</td>
                  <td>{o.description}</td>
                  <td>
                    {/* Бейдж статуса с динамическим цветом */}
                    <span className={`status-badge ${getStatusColor(o.status)}`}>
                      {o.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};