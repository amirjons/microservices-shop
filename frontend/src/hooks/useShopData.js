import { useState, useCallback, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';

// Кастомный хук для управления данными магазина
export const useShopData = (apiUrl, userId, darkMode) => {
  // Состояния для хранения данных
  const [account, setAccount] = useState(null);
  const [orders, setOrders] = useState([]);

  // Состояние загрузки
  const [loading, setLoading] = useState({ account: true, orders: true });

  // Функция получения данных с бэкенда
  const fetchData = useCallback(async () => {
    try {
      // Используем Promise.all для параллельного выполнения запросов к API
      const [accRes, ordRes] = await Promise.all([
        // Запрашиваем счет. Если 404 (нет счета) - возвращаем null, это не ошибка системы
        axios.get(`${apiUrl}/api/payments/accounts`, { headers: { 'X-User-ID': userId } }).catch(() => null),
        // Запрашиваем заказы. Если ошибка - возвращаем пустой массив
        axios.get(`${apiUrl}/api/orders/orders`, { headers: { 'X-User-ID': userId } }).catch(() => ({ data: [] }))
      ]);

      // Обновляем состояния
      setAccount(accRes?.data || null);
      setOrders(ordRes?.data || []);
    } catch (e) {
      console.error('Ошибка при загрузке данных:', e);
    } finally {
      // Выключаем индикаторы загрузки
      setLoading({ account: false, orders: false });
    }
  }, [apiUrl, userId]);

  // Загружаем данные при монтировании или смене пользователя
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Объект с действиями
  const actions = {
    // Создание нового счета
    createAccount: async () => {
      try {
        await axios.post(`${apiUrl}/api/payments/accounts`, {}, { headers: { 'X-User-ID': userId } });
        await fetchData(); // Обновляем интерфейс
        toast.success('Счет успешно создан!', { theme: darkMode ? "dark" : "colored" });
      } catch (e) {
        toast.error('Не удалось создать счет. Возможно, он уже существует.');
      }
    },

    // Пополнение счета
    topupAccount: async (amount) => {
      try {
        await axios.post(`${apiUrl}/api/payments/accounts/topup`, { amount }, { headers: { 'X-User-ID': userId } });
        await fetchData(); // Обновляем баланс
        toast.success(`Баланс пополнен на ${amount} ₽`, { theme: darkMode ? "dark" : "colored" });
      } catch (e) {
        toast.error('Ошибка при пополнении счета');
      }
    },

    // Создание нового заказа
    createOrder: async (form) => {
      try {
        await axios.post(`${apiUrl}/api/orders/orders`, form, { headers: { 'X-User-ID': userId } });
        toast.success('Заказ успешно оформлен! Ожидайте обработки...', { theme: darkMode ? "dark" : "colored" });
        // Небольшая задержка перед обновлением списка, чтобы успела пройти асинхронная обработка
        setTimeout(fetchData, 1000);
      } catch (e) {
        toast.error('Не удалось создать заказ. Проверьте данные.');
      }
    }
  };

  // Возвращаем данные и функции для использования в компонентах
  return { account, orders, loading, fetchData, actions };
};