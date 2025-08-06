import React from 'react';

const Header: React.FC = () => (
  <header className="bg-blue-700 text-white px-6 py-4 flex items-center justify-between shadow">
    <h1 className="text-2xl font-bold">Energy Tracking Dashboard</h1>
    <div>
      {/* Add user info, logout button, etc. here */}
    </div>
  </header>
);

export default Header;
