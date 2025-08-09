import React from 'react';

const Settings: React.FC = () => {
  return (
    <div className="px-4 sm:px-6 lg:px-8">
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-2xl font-semibold text-secondary-900">Settings</h1>
          <p className="mt-2 text-sm text-secondary-700">
            Configure your energy tracking system preferences
          </p>
        </div>
      </div>

      <div className="mt-8">
        <div className="text-center py-12">
          <h3 className="mt-2 text-sm font-medium text-secondary-900">Settings Coming Soon</h3>
          <p className="mt-1 text-sm text-secondary-500">
            System configuration and user preferences will be available here.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Settings;
