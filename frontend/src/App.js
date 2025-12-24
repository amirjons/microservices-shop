import React, { useState, useEffect } from 'react';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// Хуки
import { useShopData } from './hooks/useShopData';
import { useWebSocket } from './hooks/useWebSocket';

// Компоненты
import { Header } from './components/Header';
import { Footer } from './components/Footer';
import { Navigation } from './components/Navigation';
import { AccountTab } from './components/AccountTab';
import { OrdersTab } from './components/OrdersTab';
import { DashboardTab } from './components/DashboardTab';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws';

function App() {
  const [userId, setUserId] = useState(1);
  const [activeTab, setActiveTab] = useState('orders');
  const [darkMode, setDarkMode] = useState(() => JSON.parse(localStorage.getItem('darkMode')) || false);

  // Подключаем логику (хуки)
  const { account, orders, loading, fetchData, actions } = useShopData(API_URL, userId, darkMode);
  const wsConnected = useWebSocket(WS_URL, userId, fetchData, darkMode);

  // Эффект темы
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', darkMode ? 'dark' : 'light');
    localStorage.setItem('darkMode', JSON.stringify(darkMode));
  }, [darkMode]);

  return (
    <div className="app-container">
      <ToastContainer position="bottom-right" autoClose={1500} limit={3} hideProgressBar theme={darkMode ? "dark" : "light"} />

      <Header
        userId={userId}
        setUserId={setUserId}
        wsConnected={wsConnected}
        darkMode={darkMode}
        setDarkMode={setDarkMode}
        onRefresh={fetchData}
      />

      <Navigation activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="app-main">
        {activeTab === 'account' && (
          <AccountTab
            account={account}
            loading={loading.account}
            onCreate={actions.createAccount}
            onTopup={actions.topupAccount}
          />
        )}

        {activeTab === 'orders' && (
          <OrdersTab
            orders={orders}
            onCreate={actions.createOrder}
          />
        )}

        {activeTab === 'dashboard' && (
          <DashboardTab
            account={account}
            orders={orders}
          />
        )}
      </main>

      <Footer apiUrl={API_URL} />
    </div>
  );
}

export default App;