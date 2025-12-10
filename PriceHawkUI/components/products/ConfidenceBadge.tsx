import React from 'react';

interface ConfidenceBadgeProps {
  confidence: number; // 0-100
}

export const ConfidenceBadge: React.FC<ConfidenceBadgeProps> = ({ confidence }) => {
  // Color based on confidence level
  let colorClasses: string;
  if (confidence >= 95) {
    colorClasses = 'bg-green-100 text-green-800 border-green-200';
  } else if (confidence >= 80) {
    colorClasses = 'bg-yellow-100 text-yellow-800 border-yellow-200';
  } else {
    colorClasses = 'bg-orange-100 text-orange-800 border-orange-200';
  }

  return (
    <span
      className={`inline-flex items-center justify-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${colorClasses}`}
      title={`Match confidence: ${confidence}%`}
    >
      {confidence}%
    </span>
  );
};
