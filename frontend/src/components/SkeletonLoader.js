import React from 'react';

export const SkeletonLoader = ({ type }) => {
  if (type === 'balance') return (
    <div className="skeleton-balance">
      <div className="skeleton-item skeleton-text" style={{ width: '40%', height: '20px' }}></div>
      <div className="skeleton-item skeleton-text" style={{ width: '60%', height: '48px', marginTop: '12px' }}></div>
    </div>
  );
  // Можно добавить другие типы (table, stats) при желании
  return <div className="skeleton-item" style={{ height: '100px' }}></div>;
};