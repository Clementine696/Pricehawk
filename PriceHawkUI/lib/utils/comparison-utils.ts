/**
 * Comparison Utility Functions
 * Helper functions for manual comparison feature
 */

import { CompetitorRetailer } from '@/lib/types/manual-comparison';
import { COMPETITOR_DOMAINS, THAIWATSADU_DOMAINS } from '@/lib/constants/competitors';

/**
 * Detect if input is SKU or URL
 */
export function detectInputType(input: string): 'sku' | 'url' {
  const trimmed = input.trim();

  // Check if it looks like a URL
  if (trimmed.startsWith('http://') || trimmed.startsWith('https://') || trimmed.includes('.')) {
    return 'url';
  }

  // Default to SKU (typically numeric or alphanumeric)
  return 'sku';
}

/**
 * Validate Thaiwatsadu URL
 */
export function validateThaiwatsuduUrl(url: string): boolean {
  try {
    const urlObj = new URL(url);
    const hostname = urlObj.hostname.toLowerCase();
    return THAIWATSADU_DOMAINS.some(domain => hostname === domain || hostname.endsWith('.' + domain));
  } catch {
    return false;
  }
}

/**
 * Validate competitor URL matches expected domain
 */
export function validateCompetitorUrl(url: string, competitor: CompetitorRetailer): boolean {
  if (!url || url.trim() === '') return true; // Empty is valid (optional)

  try {
    const urlObj = new URL(url);
    const hostname = urlObj.hostname.toLowerCase();
    const validDomains = COMPETITOR_DOMAINS[competitor] || [];
    return validDomains.some(domain => hostname === domain || hostname.endsWith('.' + domain));
  } catch {
    return false;
  }
}

/**
 * Extract SKU from Thaiwatsadu URL
 */
export function extractSkuFromUrl(url: string): string | null {
  try {
    const urlObj = new URL(url);

    // Pattern: /product/SKU or /p/SKU
    const pathParts = urlObj.pathname.split('/').filter(Boolean);
    const productIndex = pathParts.findIndex(p => p === 'product' || p === 'p');

    if (productIndex !== -1 && pathParts[productIndex + 1]) {
      return pathParts[productIndex + 1];
    }

    // Try to extract from query params
    const skuParam = urlObj.searchParams.get('sku') || urlObj.searchParams.get('id');
    if (skuParam) return skuParam;

    // Last segment might be SKU
    const lastSegment = pathParts[pathParts.length - 1];
    if (lastSegment && /^[a-zA-Z0-9-_]+$/.test(lastSegment)) {
      return lastSegment;
    }

    return null;
  } catch {
    return null;
  }
}

/**
 * Get color class for confidence percentage
 */
export function getConfidenceColor(confidence: number): string {
  if (confidence >= 95) return 'text-green-600 bg-green-100';
  if (confidence >= 80) return 'text-yellow-600 bg-yellow-100';
  if (confidence >= 60) return 'text-orange-600 bg-orange-100';
  return 'text-red-600 bg-red-100';
}

/**
 * Get status color classes
 */
export function getMatchStatusColor(status: 'match' | 'not_match' | 'pending' | 'error'): {
  bg: string;
  text: string;
  border: string;
} {
  switch (status) {
    case 'match':
      return { bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200' };
    case 'not_match':
      return { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' };
    case 'pending':
      return { bg: 'bg-gray-50', text: 'text-gray-700', border: 'border-gray-200' };
    case 'error':
      return { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' };
    default:
      return { bg: 'bg-gray-50', text: 'text-gray-700', border: 'border-gray-200' };
  }
}

/**
 * Format price in Thai Baht
 */
export function formatThaiPrice(price: number): string {
  return new Intl.NumberFormat('th-TH', {
    style: 'currency',
    currency: 'THB',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(price);
}

/**
 * Validate SKU format (alphanumeric, 5-15 characters)
 */
export function validateSku(sku: string): boolean {
  const trimmed = sku.trim();
  return /^[a-zA-Z0-9-_]{3,20}$/.test(trimmed);
}

/**
 * Generate mock comparison ID
 */
export function generateComparisonId(): string {
  return `cmp-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`;
}
