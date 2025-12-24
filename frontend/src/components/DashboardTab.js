import React from 'react';

// Компонент вкладки "Дашборд" для отображения общей статистики по аккаунту
export const DashboardTab = ({ account, orders }) => {
  // Вычисляем общее количество заказов в истории
  const total = orders.length;

  // Фильтруем заказы, чтобы найти количество успешно завершенных
  const success = orders.filter(o => o.status === 'FINISHED').length;

  // Считаем общую сумму потраченных средств
  const spent = orders
    .filter(o => o.status === 'FINISHED')
    .reduce((a, b) => a + b.amount, 0);

  return (
    <div className="tab-content fade-in">
      {/* Сетка с карточками быстрой статистики */}
      <div className="stats-grid">

        {/* Карточка текущего баланса */}
        <div className="stat-card stat-balance">
          <div>
            <p className="stat-label">Текущий баланс</p>
            {/* Если account еще не загружен, показываем 0 */}
            <p className="stat-value">{account?.balance || 0} ₽</p>
          </div>
          <div className="stat-icon">💰</div>
        </div>

        {/* Карточка общего числа заказов */}
        <div className="stat-card stat-orders">
          <div>
            <p className="stat-label">Всего заказов</p>
            <p className="stat-value">{total}</p>
          </div>
          <div className="stat-icon">📦</div>
        </div>

        {/* Карточка количества успешных покупок */}
        <div className="stat-card stat-success">
          <div>
            <p className="stat-label">Успешных заказов</p>
            <p className="stat-value">{success}</p>
          </div>
          <div className="stat-icon">✅</div>
        </div>
      </div>

      {/* Нижняя карточка с итоговой суммой */}
      <div className="card">
        <h3>Общая сумма расходов: <span className="spent-amount">{spent} ₽</span></h3>
      </div>
    </div>
  );
};