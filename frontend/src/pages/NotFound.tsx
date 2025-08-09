import React from 'react';
import { Link } from 'react-router-dom';

const NotFound: React.FC = () => (
  <div className="flex flex-col items-center justify-center h-screen bg-gray-50">
    <h1 className="text-4xl font-bold mb-4">404 - Page Not Found</h1>
    <p className="mb-6 text-gray-600">Sorry, the page you are looking for does not exist.</p>
    <Link to="/dashboard" className="text-blue-600 hover:underline">Go to Dashboard</Link>
  </div>
);

export default NotFound;
