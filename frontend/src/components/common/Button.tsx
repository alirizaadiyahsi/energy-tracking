import React from 'react';

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'danger';
};

const base = 'px-4 py-2 rounded font-semibold focus:outline-none transition';
const variants = {
  primary: 'bg-blue-600 text-white hover:bg-blue-700',
  secondary: 'bg-gray-200 text-gray-800 hover:bg-gray-300',
  danger: 'bg-red-600 text-white hover:bg-red-700',
};

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  ...props
}) => (
  <button className={`${base} ${variants[variant]}`} {...props}>
    {children}
  </button>
);

export default Button;
