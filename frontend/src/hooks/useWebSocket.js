import { useEffect, useState, useRef } from 'react';
import { toast } from 'react-toastify';

// Кастомный хук для управления WebSocket соединением
export const useWebSocket = (url, userId, onOrderUpdate, darkMode) => {
  // Состояние подключения (для отображения индикатора Online/Offline)
  const [isConnected, setIsConnected] = useState(false);
  // Используем useRef, чтобы хранить объект сокета между рендерами без вызова перерисовки
  const wsRef = useRef(null);

  useEffect(() => {
    // Функция создания соединения
    const connect = () => {
      try {
        // Инициализация WebSocket с передачей ID пользователя
        const ws = new WebSocket(`${url}/${userId}`);
        wsRef.current = ws;

        // Обработчик успешного подключения
        ws.onopen = () => {
          setIsConnected(true);
          toast.success('✅ Соединение с сервером установлено!', {
            position: "bottom-right",
            theme: darkMode ? "dark" : "colored",
            autoClose: 1000,
            hideProgressBar: true
          });
        };

        // Обработчик входящих сообщений
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);

            // Если пришло событие об обновлении заказа
            if (data.type === 'order_update') {
              // Не показываем уведомление для статуса NEW,
              // но показываем для FINISHED или CANCELLED
              if (data.status !== 'NEW') {
                toast.info(`🔄 Статус заказа #${data.order_id} обновлен: ${data.status}`, {
                  position: "bottom-right",
                  autoClose: 1000,
                  hideProgressBar: true,
                  theme: darkMode ? "dark" : "colored"
                });
              }
              // Вызываем функцию обновления данных ,
              // чтобы в таблице обновились статусы и баланс
              if (onOrderUpdate) onOrderUpdate();
            }
          } catch (e) {
            console.error('Ошибка обработки сообщения WebSocket:', e);
          }
        };

        // Обработчик закрытия соединения
        ws.onclose = () => {
          setIsConnected(false);
          console.log('Соединение разорвано. Попытка переподключения...');
          // Пытаемся восстановить соединение через 3 секунды
          setTimeout(connect, 3000);
        };
      } catch (e) {
        console.error('Ошибка при создании WebSocket:', e);
      }
    };

    connect();

    // Функция очистки при размонтировании компонента
    return () => wsRef.current?.close();
  }, [url, userId, onOrderUpdate, darkMode]);

  return isConnected;
};