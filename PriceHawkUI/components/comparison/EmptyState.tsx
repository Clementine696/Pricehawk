'use client';

import { LucideIcon } from 'lucide-react';
import { ReactNode } from 'react';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export function EmptyState({ icon: Icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      {/* Icon */}
      <div className="mb-4">
        <Icon className="w-12 h-12 text-gray-400" />
      </div>

      {/* Title */}
      <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>

      {/* Description */}
      <p className="text-sm text-gray-500 max-w-sm mb-6">{description}</p>

      {/* Optional Action Button */}
      {action && (
        <button
          type="button"
          onClick={action.onClick}
          className="px-4 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition-colors font-medium text-sm"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}
