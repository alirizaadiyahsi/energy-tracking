import React from 'react';
import { NavLink } from 'react-router-dom';

const Navigation: React.FC = () => (
  <nav className="flex flex-col gap-2">
    <NavLink to="/dashboard" className={({ isActive }) => isActive ? 'font-bold text-blue-700' : ''}>Dashboard</NavLink>
    <NavLink to="/devices" className={({ isActive }) => isActive ? 'font-bold text-blue-700' : ''}>Devices</NavLink>
    <NavLink to="/analytics" className={({ isActive }) => isActive ? 'font-bold text-blue-700' : ''}>Analytics</NavLink>
    <NavLink to="/settings" className={({ isActive }) => isActive ? 'font-bold text-blue-700' : ''}>Settings</NavLink>
  </nav>
);

export default Navigation;
