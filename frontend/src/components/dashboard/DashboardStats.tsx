import React from 'react';
import Card from '../common/Card';

type StatProps = {
  label: string;
  value: string | number;
  icon?: React.ReactNode;
};

const DashboardStats: React.FC<{ stats: StatProps[] }> = ({ stats }) => (
  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
    {stats.map((stat, idx) => (
      <Card key={idx} className="flex items-center gap-4">
        {stat.icon && <span className="text-3xl">{stat.icon}</span>}
        <div>
          <div className="text-lg font-semibold">{stat.value}</div>
          <div className="text-gray-500 text-sm">{stat.label}</div>
        </div>
      </Card>
    ))}
  </div>
);

export default DashboardStats;
