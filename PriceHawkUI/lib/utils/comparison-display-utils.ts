import { Check, AlertTriangle, Minus } from 'lucide-react';

/**
 * Calculate price difference between Thai Watsadu and competitor
 */
export function calculatePriceDifference(
  thaiWatsuduPrice: number,
  competitorPrice: number
): {
  amountDifference: number;
  percentageDifference: number;
  status: 'cheaper' | 'more-expensive' | 'same';
} {
  const amountDifference = Math.abs(thaiWatsuduPrice - competitorPrice);
  const percentageDifference =
    competitorPrice > 0
      ? ((amountDifference / competitorPrice) * 100)
      : 0;

  let status: 'cheaper' | 'more-expensive' | 'same';
  if (Math.abs(thaiWatsuduPrice - competitorPrice) < 0.01) {
    status = 'same';
  } else if (thaiWatsuduPrice < competitorPrice) {
    status = 'cheaper';
  } else {
    status = 'more-expensive';
  }

  return {
    amountDifference,
    percentageDifference,
    status,
  };
}

/**
 * Get Tailwind color classes based on comparison status
 */
export function getComparisonColor(status: 'cheaper' | 'more-expensive' | 'same'): {
  text: string;
  bg: string;
  border: string;
} {
  switch (status) {
    case 'cheaper':
      return {
        text: 'text-green-700',
        bg: 'bg-green-50',
        border: 'border-green-200',
      };
    case 'more-expensive':
      return {
        text: 'text-red-700',
        bg: 'bg-red-50',
        border: 'border-red-200',
      };
    case 'same':
      return {
        text: 'text-gray-700',
        bg: 'bg-gray-50',
        border: 'border-gray-200',
      };
  }
}

/**
 * Format number as Thai currency
 */
export function formatThaiCurrency(amount: number): string {
  return `฿${amount.toLocaleString('th-TH', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  })}`;
}

/**
 * Get appropriate icon component for attribute
 */
export function getAttributeIcon(
  attributeName: string,
  hasValue: boolean
): typeof Check | typeof Minus | typeof AlertTriangle {
  if (!hasValue) {
    return Minus;
  }

  // Warning icon for price-related attributes with significant differences
  if (attributeName.toLowerCase().includes('price') ||
      attributeName.toLowerCase().includes('difference')) {
    return AlertTriangle;
  }

  // Checkmark for attributes with values
  return Check;
}

/**
 * Check if price difference is significant (> 5%)
 */
export function isSignificantPriceDifference(percentage: number): boolean {
  return Math.abs(percentage) > 5;
}

/**
 * Format percentage with sign
 */
export function formatPercentage(percentage: number): string {
  const sign = percentage > 0 ? '+' : '';
  return `${sign}${percentage.toFixed(1)}%`;
}

/**
 * Get display text for price difference
 */
export function getPriceDifferenceText(
  thaiWatsuduPrice: number,
  competitorPrice: number,
  competitorName: string
): string {
  const { amountDifference, status } = calculatePriceDifference(
    thaiWatsuduPrice,
    competitorPrice
  );

  if (status === 'same') {
    return 'Same price';
  }

  const formattedDiff = formatThaiCurrency(amountDifference);

  if (status === 'cheaper') {
    return `${formattedDiff} cheaper than ${competitorName}`;
  } else {
    return `${formattedDiff} more expensive than ${competitorName}`;
  }
}
