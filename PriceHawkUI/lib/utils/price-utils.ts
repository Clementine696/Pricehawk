import { PriceStatus, Retailer, ProductComparison } from '../types/price-comparison';

export type PriceComparisonCategory = 'cheapest' | 'same' | 'higher';

/**
 * Get price comparison category based on comparison with minimum price
 * @param price - The price to categorize
 * @param allValidPrices - Array of all valid prices in the row
 * @returns PriceComparisonCategory - 'cheapest' | 'same' | 'higher'
 */
export function getPriceComparisonCategory(
  price: number | null,
  allValidPrices: number[]
): PriceComparisonCategory | null {
  // Return null if price is invalid or no valid prices to compare
  if (!price || price <= 0 || allValidPrices.length === 0) {
    return null;
  }

  const minPrice = Math.min(...allValidPrices);

  // Define threshold for "same" (within 2%)
  const threshold = 0.02;

  // Cheapest if equal to minimum
  if (price === minPrice) {
    return 'cheapest';
  }

  // Same if within 2% of minimum
  if (price <= minPrice * (1 + threshold)) {
    return 'same';
  }

  // Otherwise, it's higher
  return 'higher';
}

/**
 * Calculate price status by comparing Thai Watsadu price with competitors
 * @param thaiWatsaduPrice - Thai Watsadu's price
 * @param competitorPrices - Array of competitor prices (excluding null values)
 * @returns PriceStatus - 'cheapest' | 'higher' | 'same' | 'unavailable'
 */
export function calculateStatus(
  thaiWatsaduPrice: number | null,
  competitorPrices: (number | null)[]
): PriceStatus {
  // Filter out null prices
  const validPrices = competitorPrices.filter((p): p is number => p !== null && p > 0);

  // If Thai Watsadu price is null or no competitor prices available
  if (!thaiWatsaduPrice || thaiWatsaduPrice <= 0 || validPrices.length === 0) {
    return 'unavailable';
  }

  const minCompetitorPrice = Math.min(...validPrices);
  const maxCompetitorPrice = Math.max(...validPrices);

  // Define threshold for "same" (within 2%)
  const threshold = 0.02;

  if (thaiWatsaduPrice <= minCompetitorPrice * (1 + threshold)) {
    return 'cheapest';  // Green badge
  } else if (thaiWatsaduPrice >= maxCompetitorPrice * (1 - threshold)) {
    return 'higher';    // Yellow/Orange badge
  } else {
    return 'same';      // Gray badge
  }
}

/**
 * Find the lowest price among all retailers
 * @param prices - Object containing prices from all retailers
 * @returns Lowest price or null if no valid prices
 */
export function findLowestPrice(
  prices: ProductComparison['prices']
): number | null {
  const allPrices = Object.values(prices)
    .map(p => p.price)
    .filter((p): p is number => p !== null && p > 0);

  return allPrices.length > 0 ? Math.min(...allPrices) : null;
}

/**
 * Find the highest price among all retailers
 * @param prices - Object containing prices from all retailers
 * @returns Highest price or null if no valid prices
 */
export function findHighestPrice(
  prices: ProductComparison['prices']
): number | null {
  const allPrices = Object.values(prices)
    .map(p => p.price)
    .filter((p): p is number => p !== null && p > 0);

  return allPrices.length > 0 ? Math.max(...allPrices) : null;
}

/**
 * Calculate percentage difference between two prices
 * @param price1 - First price
 * @param price2 - Second price (base for percentage calculation)
 * @returns Percentage difference or null if invalid
 */
export function calculatePriceDifference(
  price1: number | null,
  price2: number | null
): number | null {
  if (!price1 || !price2 || price2 === 0) return null;

  return ((price1 - price2) / price2) * 100;
}

/**
 * Format number as Thai Baht currency
 * @param amount - Amount to format
 * @param showSymbol - Whether to show ฿ symbol (default: true)
 * @returns Formatted currency string
 */
export function formatCurrency(
  amount: number | null,
  showSymbol: boolean = true
): string {
  if (amount === null || amount === undefined) return '-';

  const formatted = new Intl.NumberFormat('th-TH', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(amount);

  return showSymbol ? `฿${formatted}` : formatted;
}

/**
 * Format date using Thai locale
 * @param dateString - ISO date string
 * @param options - Intl.DateTimeFormatOptions
 * @returns Formatted date string
 */
export function formatDate(
  dateString: string,
  options?: Intl.DateTimeFormatOptions
): string {
  const date = new Date(dateString);

  const defaultOptions: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  };

  return new Intl.DateTimeFormat('th-TH', options || defaultOptions).format(date);
}

/**
 * Get status badge color class
 * @param status - Price status
 * @returns Tailwind color classes
 */
export function getStatusColor(status: PriceStatus): string {
  switch (status) {
    case 'cheapest':
      return 'bg-green-500 text-white';
    case 'higher':
      return 'bg-amber-500 text-white';
    case 'same':
      return 'bg-gray-200 text-gray-700';
    case 'unavailable':
      return 'bg-gray-300 text-gray-600';
    default:
      return 'bg-gray-300 text-gray-700';
  }
}

/**
 * Get status badge label
 * @param status - Price status
 * @returns Label text (English)
 */
export function getStatusLabel(status: PriceStatus): string {
  switch (status) {
    case 'cheapest':
      return 'Cheapest';
    case 'higher':
      return 'Higher';
    case 'same':
      return 'Same';
    case 'unavailable':
      return 'N/A';
    default:
      return 'Unknown';
  }
}
