// Retailer enum
export enum Retailer {
  THAI_WATSADU = 'thai_watsadu',
  HOMEPRO = 'homepro',
  GLOBAL_HOUSE = 'global_house',
  DOHOME = 'dohome',
  BOONTHAVORN = 'boonthavorn',
}

// Retailer display names (Thai + English)
export const RetailerNames: Record<Retailer, { th: string; en: string }> = {
  [Retailer.THAI_WATSADU]: { th: 'ไทวัสดุ', en: 'Thai Watsadu' },
  [Retailer.HOMEPRO]: { th: 'โฮมโปร', en: 'HomePro' },
  [Retailer.GLOBAL_HOUSE]: { th: 'โกลบอลเฮ้าส์', en: 'Global House' },
  [Retailer.DOHOME]: { th: 'ดูโฮม', en: 'DoHome' },
  [Retailer.BOONTHAVORN]: { th: 'บุญถาวร', en: 'Boonthavorn' },
};

// Price status type
export type PriceStatus = 'cheapest' | 'higher' | 'same' | 'unavailable';

// Validation status type
export type ValidationStatus = 'pending' | 'correct' | 'incorrect';

// Individual retailer price info
export interface RetailerPrice {
  retailer: Retailer;
  price: number | null;        // null if unavailable
  originalPrice?: number;      // for discount calculation
  currency: 'THB';
  productUrl: string | null;   // URL to product page
  lastUpdated: string;         // ISO date string
  inStock: boolean;
  promoText?: string;          // e.g., "ลด 20%"
}

// Product comparison entry
export interface ProductComparison {
  id: string;
  sku: string;
  name: string;
  nameTh?: string;             // Thai name if available
  description?: string;        // Product description
  descriptionTh?: string;      // Thai product description
  category: string;
  categoryTh?: string;         // Thai category name
  brand: string;
  imageUrl: string;

  // Prices from each retailer
  prices: {
    [Retailer.THAI_WATSADU]: RetailerPrice;
    [Retailer.HOMEPRO]: RetailerPrice;
    [Retailer.GLOBAL_HOUSE]: RetailerPrice;
    [Retailer.DOHOME]: RetailerPrice;
    [Retailer.BOONTHAVORN]: RetailerPrice;
  };

  // Computed fields
  status: PriceStatus;
  lowestPrice: number | null;
  highestPrice: number | null;
  priceDifferencePercent: number | null;  // % difference between Thai Watsadu and lowest competitor
}

// Filter state
export interface ProductFilterState {
  search: string;
  category: string | null;
  brand: string | null;
  status: PriceStatus | null;
  sortBy: 'name' | 'sku' | 'category' | 'brand' | 'price' | 'status';
  sortOrder: 'asc' | 'desc';
}

// Pagination state
export interface PaginationState {
  page: number;
  pageSize: number;
  total: number;
}

// GET /api/products/comparison
export interface ProductComparisonListResponse {
  products: ProductComparison[];
  pagination: {
    page: number;
    pageSize: number;
    total: number;
    totalPages: number;
  };
  filters: {
    categories: { value: string; label: string; count: number }[];
    brands: { value: string; label: string; count: number }[];
  };
  summary: {
    totalProducts: number;
    cheapestCount: number;
    higherCount: number;
    sameCount: number;
    unavailableCount: number;
  };
}

// Matched product interface
export interface MatchedProduct {
  id: string;
  name: string;
  sku: string;
  imageUrl: string;
  price: number;
  url: string;
  description?: string;
  brand?: string;
  category?: string;
  validationStatus?: ValidationStatus;
  isManualEntry?: boolean;
}

// Retailer match with multiple products
export interface RetailerMatch {
  retailer: Retailer;
  confidence: number;        // 0-100%
  matchType: 'exact' | 'similar';
  products: MatchedProduct[];
}

// Legacy single product match format (for API compatibility)
export interface LegacyMatchedProduct {
  retailer: Retailer;
  confidence: number;
  matchType: 'exact' | 'similar';
  product: {
    name: string;
    sku: string;
    imageUrl: string;
    price: number;
    url: string;
    description?: string;
    brand?: string;
    category?: string;
    inStock?: boolean;
  };
}

// GET /api/products/comparison/:id
export interface ProductComparisonDetailResponse {
  product: ProductComparison;
  priceHistory: {
    date: string;
    prices: Record<Retailer, number | null>;
  }[];
  matchedProducts: (RetailerMatch | LegacyMatchedProduct)[];
}
