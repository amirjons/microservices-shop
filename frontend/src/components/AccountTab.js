import React, { useState } from 'react';
import { SkeletonLoader } from './SkeletonLoader';

export const AccountTab = ({ account, loading, onCreate, onTopup }) => {
  // Локальное состояние для хранения введенной суммы пополнения
  const [amount, setAmount] = useState('');

  // Если данные загружаются, показываем анимацию загрузки (скелетон)
  if (loading) return <div className="card"><SkeletonLoader type="balance" /></div>;

  // Если аккаунт не существует (null), показываем интерфейс для его создания
  if (!account) return (
    <div className="card empty-state">
      <div className="empty-icon">⚠️</div>
      <h3>Счет не найден</h3>
      <p className="empty-text">Для начала работы необходимо создать счет</p>
      <button onClick={onCreate} className="btn-primary btn-large">+ Создать счет</button>
    </div>
  );

  // Основной интерфейс управления счетом
  return (
    <div className="card account-card">
      <h2 className="card-title">💰 Управление счетом</h2>
      <div className="account-content">

        {/* Карточка с текущим балансом */}
        <div className="balance-card">
          <div>
            <p className="balance-label">Текущий баланс</p>
            <p className="balance-amount">{account.balance} ₽</p>
            <p className="balance-id">ID счета: {account.id}</p>
          </div>
          <div className="balance-icon">💰</div>
        </div>

        {/* Секция пополнения счета */}
        <div className="topup-section">
          <h3>Пополнить счет</h3>
          <div className="topup-form">
            <input
              type="number"
              value={amount}
              onChange={e => setAmount(e.target.value)}
              placeholder="Введите сумму"
            />
            <button
              onClick={() => {
                // Вызываем функцию пополнения и очищаем поле ввода
                onTopup(parseFloat(amount));
                setAmount('');
              }}
              className="btn-success"
            >
              Пополнить
            </button>
          </div>

          {/* Кнопки быстрого выбора суммы */}
          <div className="quick-amounts">
            {[100, 500, 1000, 5000].map(val => (
              <button
                key={val}
                onClick={() => setAmount(val)}
                className="btn-amount"
              >
                +{val} ₽
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};