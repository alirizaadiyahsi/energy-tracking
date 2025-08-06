import React from 'react';
import Navigation from './Navigation';

const Sidebar: React.FC = () => (
  <aside className="w-64 bg-gray-100 h-full p-4 border-r">
    <Navigation />
  </aside>
);

export default Sidebar;
