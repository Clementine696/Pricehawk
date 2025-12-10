import React from 'react';
import { PriceStatus } from '@/lib/types/price-comparison';
import { getStatusColor, getStatusLabel } from '@/lib/utils/price-utils';

interface StatusBadgeProps {
  status: PriceStatus;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const colorClasses = getStatusColor(status);
  const label = getStatusLabel(status);

  return (
    <span
      className={`inline-flex items-center justify-center px-3 py-1 rounded-full text-xs font-medium ${colorClasses}`}
    >
      {label}
    </span>
  );
};
