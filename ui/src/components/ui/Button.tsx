'use client';

import React from 'react';
import { Loader2 } from 'lucide-react';

type Variant = 'primary' | 'danger' | 'success' | 'outline' | 'ghost' | 'outline-success' | 'outline-primary';
type Size = 'sm' | 'md' | 'lg';

const VARIANT_CLASSES: Record<Variant, string> = {
  primary:         'bg-cyan-500 text-white hover:bg-cyan-600 focus:ring-cyan-500',
  danger:          'bg-red-500 text-white hover:bg-red-600 focus:ring-red-500',
  success:         'bg-emerald-500 text-white hover:bg-emerald-600 focus:ring-emerald-500',
  outline:         'border border-gray-300 text-gray-700 bg-white hover:bg-gray-50 focus:ring-gray-300',
  ghost:           'text-gray-700 hover:bg-gray-100 focus:ring-gray-300',
  'outline-success': 'border border-green-600 text-green-600 bg-white hover:bg-green-50 focus:ring-green-500',
  'outline-primary': 'border border-cyan-600 text-cyan-600 bg-white hover:bg-cyan-50 focus:ring-cyan-500',
};

const SIZE_CLASSES: Record<Size, string> = {
  sm: 'px-3 py-1 text-sm rounded',
  md: 'px-4 py-2 text-sm rounded-lg',
  lg: 'px-6 py-2 rounded-lg',
};

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  icon?: React.ReactNode;
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  disabled,
  className = '',
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      disabled={disabled || loading}
      className={[
        'inline-flex items-center justify-center gap-2 font-medium transition-colors',
        'focus:outline-none focus:ring-2 focus:ring-offset-2',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        'whitespace-nowrap',
        VARIANT_CLASSES[variant],
        SIZE_CLASSES[size],
        className,
      ].join(' ')}
      {...props}
    >
      {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : icon}
      {children}
    </button>
  );
}
