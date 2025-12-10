'use client';

import React from 'react';
import { formatThaiCurrency } from '@/lib/utils/comparison-display-utils';

interface PriceDifferenceDisplayProps {
  thaiWatsuduPrice: number;
  competitorPrice: number;
  competitorName: string;
  showLargePrice?: boolean;
}

export function PriceDifferenceDisplay({
  thaiWatsuduPrice,
  competitorPrice,
  competitorName,
  showLargePrice = true,
}: PriceDifferenceDisplayProps) {
  return (
    <div className="flex flex-col items-center justify-center py-2">
      {showLargePrice && (
        <div className="text-2xl font-bold text-gray-900">
          {formatThaiCurrency(competitorPrice)}
        </div>
      )}
    </div>
  );
}
