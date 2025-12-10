import React from 'react';

interface MatchTypeBadgeProps {
  matchType: 'exact' | 'similar';
}

export const MatchTypeBadge: React.FC<MatchTypeBadgeProps> = ({ matchType }) => {
  const isExact = matchType === 'exact';

  const colorClasses = isExact
    ? 'bg-green-100 text-green-800 border-green-200'
    : 'bg-amber-100 text-amber-800 border-amber-200';

  const label = isExact ? 'Exact' : 'Similar';

  return (
    <span
      className={`inline-flex items-center justify-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${colorClasses}`}
      title={isExact ? 'Exact product match' : 'Similar product match'}
    >
      {label}
    </span>
  );
};
