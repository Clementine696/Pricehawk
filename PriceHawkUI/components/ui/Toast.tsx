'use client';

import { useEffect } from 'react';
import { X, CheckCircle, XCircle } from 'lucide-react';
import { createPortal } from 'react-dom';

export type ToastVariant = 'success' | 'error';

interface ToastProps {
  message: string;
  variant?: ToastVariant;
  isVisible: boolean;
  onClose: () => void;
  duration?: number;
}

export function Toast({
  message,
  variant = 'success',
  isVisible,
  onClose,
  duration = 4000,
}: ToastProps) {
  useEffect(() => {
    if (isVisible && duration > 0) {
      const timer = setTimeout(() => {
        onClose();
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [isVisible, duration, onClose]);

  if (!isVisible) return null;

  const variantStyles = {
    success: {
      bg: 'bg-white',
      border: 'border-cyan-500',
      icon: <CheckCircle className="w-5 h-5 text-cyan-500" />,
      text: 'text-gray-900',
    },
    error: {
      bg: 'bg-white',
      border: 'border-red-500',
      icon: <XCircle className="w-5 h-5 text-red-500" />,
      text: 'text-gray-900',
    },
  };

  const styles = variantStyles[variant];

  const toastElement = (
    <div
      className={`
        fixed top-4 right-4 z-50
        ${styles.bg} ${styles.border} border-l-4
        shadow-lg rounded-lg overflow-hidden
        min-w-[320px] max-w-md
        animate-slide-in-right
      `}
      role="alert"
      aria-live="polite"
    >
      <div className="flex items-start gap-3 p-4">
        {/* Icon */}
        <div className="flex-shrink-0">{styles.icon}</div>

        {/* Message */}
        <div className={`flex-1 ${styles.text} text-sm font-medium`}>
          {message}
        </div>

        {/* Close Button */}
        <button
          type="button"
          onClick={onClose}
          className="flex-shrink-0 text-gray-400 hover:text-gray-600 transition-colors"
          aria-label="Close notification"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Progress Bar */}
      {duration > 0 && (
        <div className="h-1 bg-gray-100">
          <div
            className={`h-full ${
              variant === 'success' ? 'bg-cyan-500' : 'bg-red-500'
            }`}
            style={{
              animation: `shrink ${duration}ms linear forwards`,
            }}
          />
        </div>
      )}
    </div>
  );

  // Use portal to render toast at document body level
  if (typeof document !== 'undefined') {
    return createPortal(toastElement, document.body);
  }

  return null;
}

// CSS animations (add to globals.css if not present)
// @keyframes slide-in-right {
//   from {
//     transform: translateX(100%);
//     opacity: 0;
//   }
//   to {
//     transform: translateX(0);
//     opacity: 1;
//   }
// }
//
// @keyframes shrink {
//   from {
//     width: 100%;
//   }
//   to {
//     width: 0%;
//   }
// }
