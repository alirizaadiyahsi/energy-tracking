import React from 'react';

const Analytics: React.FC = () => {
  return (
    <div className="px-4 sm:px-6 lg:px-8">
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-2xl font-semibold text-secondary-900">Analytics</h1>
          <p className="mt-2 text-sm text-secondary-700">
            Analyze your energy consumption patterns and trends
          </p>
        </div>
      </div>

      <div className="mt-8">
        <div className="text-center py-12">
          <h3 className="mt-2 text-sm font-medium text-secondary-900">Analytics Coming Soon</h3>
          <p className="mt-1 text-sm text-secondary-500">
            Advanced analytics and reporting features will be available here.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Analytics;
