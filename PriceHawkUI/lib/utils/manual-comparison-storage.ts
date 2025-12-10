import {
  ProductComparison,
  Retailer,
  RetailerPrice,
  PriceStatus,
} from '@/lib/types/price-comparison';

const MANUAL_PRODUCTS_KEY = 'pricehawk_manual_products';

// ComparisonTableData structure from the manual comparison API
export interface ComparisonTableProduct {
  sku: string;
  name: string;
  price: number;
  discountPercentage?: number;
  unitPrice?: number;
  imageUrl?: string;
  productUrl: string;
  brand?: string;
  category?: string;
  stockStatus?: string;
  retailer: string;
  retailerLogo?: string;
}

export interface ComparisonTableData {
  thaiWatsadu: ComparisonTableProduct;
  competitors: ComparisonTableProduct[];
}

// Check if we're on the client side
function isClient(): boolean {
  return typeof window !== 'undefined';
}

// Generate unique ID for manual product
function generateManualProductId(sku: string): string {
  const timestamp = Date.now();
  return `manual_${timestamp}_${sku}`;
}

// Map competitor retailer name to Retailer enum
function mapRetailerToEnum(retailerName: string): Retailer {
  const mapping: Record<string, Retailer> = {
    THAI_WATSADU: Retailer.THAI_WATSADU,
    HOMEPRO: Retailer.HOMEPRO,
    MEGA_HOME: Retailer.HOMEPRO, // Map MEGA_HOME to HOMEPRO for now
    GLOBAL_HOUSE: Retailer.GLOBAL_HOUSE,
    DOHOME: Retailer.DOHOME,
    BOONTHAVORN: Retailer.BOONTHAVORN,
  };
  return mapping[retailerName] || Retailer.THAI_WATSADU;
}

// Calculate price status based on Thai Watsadu price vs competitors
function calculatePriceStatus(
  thaiWatsuduPrice: number,
  competitorPrices: (number | null)[]
): PriceStatus {
  const validPrices = competitorPrices.filter((p): p is number => p !== null);

  if (validPrices.length === 0) {
    return 'unavailable';
  }

  const minCompetitorPrice = Math.min(...validPrices);

  if (thaiWatsuduPrice < minCompetitorPrice) {
    return 'cheapest';
  } else if (thaiWatsuduPrice === minCompetitorPrice) {
    return 'same';
  } else {
    return 'higher';
  }
}

// Transform ComparisonTableData to ProductComparison format
export function transformComparisonToProduct(
  data: ComparisonTableData,
  manualId?: string
): ProductComparison {
  const id = manualId || generateManualProductId(data.thaiWatsadu.sku);
  const now = new Date().toISOString();

  // Build prices object
  const prices: ProductComparison['prices'] = {
    [Retailer.THAI_WATSADU]: {
      retailer: Retailer.THAI_WATSADU,
      price: data.thaiWatsadu.price,
      originalPrice: data.thaiWatsadu.discountPercentage
        ? Math.round(data.thaiWatsadu.price / (1 - data.thaiWatsadu.discountPercentage / 100))
        : undefined,
      currency: 'THB',
      productUrl: data.thaiWatsadu.productUrl,
      lastUpdated: now,
      inStock: data.thaiWatsadu.stockStatus === 'In Stock',
      promoText: data.thaiWatsadu.discountPercentage
        ? `ลด ${data.thaiWatsadu.discountPercentage}%`
        : undefined,
    },
    [Retailer.HOMEPRO]: {
      retailer: Retailer.HOMEPRO,
      price: null,
      currency: 'THB',
      productUrl: null,
      lastUpdated: now,
      inStock: false,
    },
    [Retailer.GLOBAL_HOUSE]: {
      retailer: Retailer.GLOBAL_HOUSE,
      price: null,
      currency: 'THB',
      productUrl: null,
      lastUpdated: now,
      inStock: false,
    },
    [Retailer.DOHOME]: {
      retailer: Retailer.DOHOME,
      price: null,
      currency: 'THB',
      productUrl: null,
      lastUpdated: now,
      inStock: false,
    },
    [Retailer.BOONTHAVORN]: {
      retailer: Retailer.BOONTHAVORN,
      price: null,
      currency: 'THB',
      productUrl: null,
      lastUpdated: now,
      inStock: false,
    },
  };

  // Fill in competitor prices
  data.competitors.forEach((competitor) => {
    const retailerEnum = mapRetailerToEnum(competitor.retailer);
    prices[retailerEnum] = {
      retailer: retailerEnum,
      price: competitor.price,
      originalPrice: competitor.discountPercentage
        ? Math.round(competitor.price / (1 - competitor.discountPercentage / 100))
        : undefined,
      currency: 'THB',
      productUrl: competitor.productUrl,
      lastUpdated: now,
      inStock: competitor.stockStatus === 'In Stock',
      promoText: competitor.discountPercentage
        ? `ลด ${competitor.discountPercentage}%`
        : undefined,
    };
  });

  // Calculate lowest and highest prices
  const allPrices = Object.values(prices)
    .map((p) => p.price)
    .filter((p): p is number => p !== null);
  const lowestPrice = allPrices.length > 0 ? Math.min(...allPrices) : null;
  const highestPrice = allPrices.length > 0 ? Math.max(...allPrices) : null;

  // Calculate price status
  const thaiWatsuduPrice = data.thaiWatsadu.price;
  const competitorPrices = data.competitors.map((c) => c.price);
  const status = calculatePriceStatus(thaiWatsuduPrice, competitorPrices);

  // Calculate price difference percentage
  let priceDifferencePercent: number | null = null;
  if (lowestPrice && lowestPrice !== thaiWatsuduPrice) {
    priceDifferencePercent = ((thaiWatsuduPrice - lowestPrice) / lowestPrice) * 100;
  }

  return {
    id,
    sku: data.thaiWatsadu.sku,
    name: data.thaiWatsadu.name,
    category: data.thaiWatsadu.category || 'Manual Entry',
    brand: data.thaiWatsadu.brand || 'Unknown',
    imageUrl: data.thaiWatsadu.imageUrl || '/placeholder-product.jpg',
    prices,
    status,
    lowestPrice,
    highestPrice,
    priceDifferencePercent,
  };
}

// Save manual comparison product
export function saveManualComparisonProduct(data: ComparisonTableData): string {
  if (!isClient()) {
    console.warn('Cannot save to localStorage on server side');
    return '';
  }

  try {
    const productId = generateManualProductId(data.thaiWatsadu.sku);
    const product = transformComparisonToProduct(data, productId);

    // Get existing products
    const existing = getAllManualComparisonProducts();

    // Add new product at the beginning (most recent first)
    const updated = [product, ...existing];

    // Save to localStorage
    localStorage.setItem(MANUAL_PRODUCTS_KEY, JSON.stringify(updated));

    return productId;
  } catch (error) {
    console.error('Failed to save manual comparison product:', error);
    return '';
  }
}

// Get all manual comparison products
export function getAllManualComparisonProducts(): ProductComparison[] {
  if (!isClient()) return [];

  try {
    const data = localStorage.getItem(MANUAL_PRODUCTS_KEY);
    if (!data) return [];

    const products = JSON.parse(data) as ProductComparison[];
    return products;
  } catch (error) {
    console.error('Failed to load manual comparison products:', error);
    return [];
  }
}

// Get manual comparison product by ID
export function getManualComparisonProductById(id: string): ProductComparison | null {
  if (!isClient()) return null;

  try {
    const products = getAllManualComparisonProducts();
    return products.find((p) => p.id === id) || null;
  } catch (error) {
    console.error('Failed to get manual comparison product:', error);
    return null;
  }
}

// Delete manual comparison product
export function deleteManualComparisonProduct(id: string): void {
  if (!isClient()) return;

  try {
    const products = getAllManualComparisonProducts();
    const filtered = products.filter((p) => p.id !== id);
    localStorage.setItem(MANUAL_PRODUCTS_KEY, JSON.stringify(filtered));
  } catch (error) {
    console.error('Failed to delete manual comparison product:', error);
  }
}

// Update manual comparison product
export function updateManualProduct(
  id: string,
  updates: Partial<ProductComparison>
): void {
  if (!isClient()) return;

  try {
    const products = getAllManualComparisonProducts();
    const index = products.findIndex((p) => p.id === id);

    if (index === -1) {
      console.warn(`Product with id ${id} not found`);
      return;
    }

    products[index] = { ...products[index], ...updates };
    localStorage.setItem(MANUAL_PRODUCTS_KEY, JSON.stringify(products));
  } catch (error) {
    console.error('Failed to update manual comparison product:', error);
  }
}

// Clear all manual products
export function clearAllManualProducts(): void {
  if (!isClient()) return;

  try {
    localStorage.removeItem(MANUAL_PRODUCTS_KEY);
  } catch (error) {
    console.error('Failed to clear manual comparison products:', error);
  }
}

// Check if a product ID is a manual entry
export function isManualProductId(id: string): boolean {
  return id.startsWith('manual_');
}
