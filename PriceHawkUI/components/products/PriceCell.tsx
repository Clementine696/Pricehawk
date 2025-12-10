import React from 'react';
import { ExternalLink } from 'lucide-react';
import { formatCurrency, PriceComparisonCategory } from '@/lib/utils/price-utils';

interface PriceCellProps {
  price: number | null;
  originalPrice?: number;
  productUrl: string | null;
  isLowest?: boolean;
  isHighest?: boolean;
  comparisonCategory?: PriceComparisonCategory | null;
  hidden?: boolean;
}

export const PriceCell: React.FC<PriceCellProps> = ({
  price,
  originalPrice,
  productUrl,
  isLowest,
  isHighest,
  comparisonCategory,
  hidden,
}) => {
  const priceText = formatCurrency(price);

  if (hidden === true || price === null) {
    return <span className="text-gray-400">-</span>;
  }

  // Use new comparison category if available, otherwise fall back to old props
  let colorClass: string;
  if (comparisonCategory) {
    switch (comparisonCategory) {
      case 'cheapest':
        colorClass = 'text-green-600 font-semibold';
        break;
      case 'same':
        colorClass = 'text-gray-500';
        break;
      case 'higher':
        colorClass = 'text-red-600';
        break;
      default:
        colorClass = 'text-gray-700';
    }
  } else {
    // Backward compatibility
    colorClass = isLowest
      ? 'text-green-600 font-semibold'
      : isHighest
      ? 'text-red-600 font-semibold'
      : 'text-cyan-500';
  }

  if (productUrl) {
    return (
      <a
        href={productUrl}
        target="_blank"
        rel="noopener noreferrer"
        className={`inline-flex items-center gap-1 hover:underline ${colorClass}`}
      >
        {priceText}
        <ExternalLink className="w-3 h-3" />
      </a>
    );
  }

  return <span className={colorClass}>{priceText}</span>;
};
