import { Retailer } from '@/lib/types/price-comparison';

export const RetailerColors: Record<Retailer, string> = {
  [Retailer.THAI_WATSADU]: 'bg-red-600',
  [Retailer.HOMEPRO]: 'bg-red-500',
  [Retailer.GLOBAL_HOUSE]: 'bg-blue-800',
  [Retailer.DOHOME]: 'bg-orange-500',
  [Retailer.BOONTHAVORN]: 'bg-green-600',
};
