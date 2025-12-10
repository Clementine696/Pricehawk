import { ValidationStatus } from '@/lib/types/price-comparison';

const STORAGE_PREFIX = 'pricehawk_validation_';
const MANUAL_COMPARISON_PREFIX = 'pricehawk_manual_';

export interface ManualComparisonData {
  retailer: string;
  productName: string;
  sku: string;
  price: number;
  url: string;
  imageUrl?: string;
  createdAt: string;
}

interface ValidationStorageData {
  statuses: Record<string, ValidationStatus>;
  updatedAt: string;
}

function getStorageKey(productId: string): string {
  return `${STORAGE_PREFIX}${productId}`;
}

function getManualComparisonKey(productId: string): string {
  return `${MANUAL_COMPARISON_PREFIX}${productId}`;
}

function isClient(): boolean {
  return typeof window !== 'undefined';
}

export function getValidationStatus(
  productId: string,
  matchedProductId: string
): ValidationStatus | null {
  if (!isClient()) return null;

  try {
    const key = getStorageKey(productId);
    const data = localStorage.getItem(key);
    if (!data) return null;

    const parsed: ValidationStorageData = JSON.parse(data);
    return parsed.statuses[matchedProductId] || null;
  } catch {
    return null;
  }
}

export function setValidationStatus(
  productId: string,
  matchedProductId: string,
  status: ValidationStatus
): void {
  if (!isClient()) return;

  try {
    const key = getStorageKey(productId);
    const existingData = localStorage.getItem(key);

    let storageData: ValidationStorageData;
    if (existingData) {
      storageData = JSON.parse(existingData);
    } else {
      storageData = {
        statuses: {},
        updatedAt: new Date().toISOString(),
      };
    }

    storageData.statuses[matchedProductId] = status;
    storageData.updatedAt = new Date().toISOString();

    localStorage.setItem(key, JSON.stringify(storageData));
  } catch (error) {
    console.error('Failed to save validation status:', error);
  }
}

export function getAllValidationStatuses(
  productId: string
): Record<string, ValidationStatus> {
  if (!isClient()) return {};

  try {
    const key = getStorageKey(productId);
    const data = localStorage.getItem(key);
    if (!data) return {};

    const parsed: ValidationStorageData = JSON.parse(data);
    return parsed.statuses;
  } catch {
    return {};
  }
}

export function getAllValidationStatusesForAllProducts(): Record<string, Record<string, ValidationStatus>> {
  if (!isClient()) return {};

  try {
    const result: Record<string, Record<string, ValidationStatus>> = {};

    // Iterate through all localStorage keys
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (!key || !key.startsWith(STORAGE_PREFIX)) continue;

      // Extract productId from key
      const productId = key.substring(STORAGE_PREFIX.length);

      // Parse the stored data
      const data = localStorage.getItem(key);
      if (!data) continue;

      const parsed: ValidationStorageData = JSON.parse(data);
      result[productId] = parsed.statuses;
    }

    return result;
  } catch (error) {
    console.error('Failed to load validation statuses:', error);
    return {};
  }
}

export function clearValidationStatuses(productId: string): void {
  if (!isClient()) return;

  try {
    const key = getStorageKey(productId);
    localStorage.removeItem(key);
  } catch (error) {
    console.error('Failed to clear validation statuses:', error);
  }
}

export function getManualComparison(
  productId: string
): ManualComparisonData | null {
  if (!isClient()) return null;

  try {
    const key = getManualComparisonKey(productId);
    const data = localStorage.getItem(key);
    if (!data) return null;

    return JSON.parse(data);
  } catch {
    return null;
  }
}

export function setManualComparison(
  productId: string,
  data: ManualComparisonData
): void {
  if (!isClient()) return;

  try {
    const key = getManualComparisonKey(productId);
    localStorage.setItem(key, JSON.stringify(data));
  } catch (error) {
    console.error('Failed to save manual comparison:', error);
  }
}

export function clearManualComparison(productId: string): void {
  if (!isClient()) return;

  try {
    const key = getManualComparisonKey(productId);
    localStorage.removeItem(key);
  } catch (error) {
    console.error('Failed to clear manual comparison:', error);
  }
}
