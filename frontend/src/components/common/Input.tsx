import React from 'react';

type InputProps = React.InputHTMLAttributes<HTMLInputElement> & {
  label?: string;
  error?: string;
};

const Input: React.FC<InputProps> = ({ label, error, ...props }) => (
  <div className="mb-4">
    {label && <label className="block mb-1 font-medium">{label}</label>}
    <input
      className={`w-full px-3 py-2 border rounded focus:outline-none focus:ring ${error ? 'border-red-500' : 'border-gray-300'}`}
      {...props}
    />
    {error && <p className="text-red-500 text-xs mt-1">{error}</p>}
  </div>
);

export default Input;
