import { NextRequest, NextResponse } from 'next/server';
import {
  ManualComparisonRequest,
  ManualComparisonRequestV2,
  ManualComparisonResponse,
  CompetitorMatchResult,
  CompetitorRetailer,
  CompetitorUrlEntry,
  SourceProduct,
  UrlComparisonResult,
  ThaiWatsuduInput,
  ComparisonTableProduct,
  ComparisonTableData,
} from '@/lib/types/manual-comparison';
import { generateComparisonId } from '@/lib/utils/comparison-utils';
import { COMPETITORS } from '@/lib/constants/competitors';

// Mock data for development - simulates competitor matching results
function generateMockResults(
  competitors: CompetitorRetailer[],
  sourceProduct: SourceProduct,
  competitorUrls?: Partial<Record<CompetitorRetailer, string>>
): CompetitorMatchResult[] {
  const mockResults: Record<CompetitorRetailer, Partial<CompetitorMatchResult>> = {
    HOMEPRO: {
      status: 'match',
      confidence: 95,
      matchedProduct: {
        sku: `HP-${sourceProduct.sku}`,
        name: sourceProduct.name,
        price: Math.round(sourceProduct.price * (1 + (Math.random() * 0.3 - 0.1))),
        imageUrl: '/mock/homepro-product.jpg',
        productUrl: competitorUrls?.HOMEPRO || `https://www.homepro.co.th/p/${sourceProduct.sku}`,
      },
    },
    MEGA_HOME: {
      status: 'match',
      confidence: 87,
      matchedProduct: {
        sku: `MH-${sourceProduct.sku}`,
        name: sourceProduct.name,
        price: Math.round(sourceProduct.price * (1 + (Math.random() * 0.3 - 0.1))),
        imageUrl: '/mock/megahome-product.jpg',
        productUrl: competitorUrls?.MEGA_HOME || `https://www.megahome.co.th/product/${sourceProduct.sku}`,
      },
    },
    BOONTHAVORN: {
      status: 'not_match',
      confidence: 0,
      errorMessage: 'No matching product found in catalog',
    },
    GLOBAL_HOUSE: {
      status: 'match',
      confidence: 92,
      matchedProduct: {
        sku: `GH-${sourceProduct.sku}`,
        name: sourceProduct.name,
        price: Math.round(sourceProduct.price * (1 + (Math.random() * 0.3 - 0.1))),
        imageUrl: '/mock/globalhouse-product.jpg',
        productUrl: competitorUrls?.GLOBAL_HOUSE || `https://www.globalhouse.co.th/product/${sourceProduct.sku}`,
      },
    },
    DOHOME: {
      status: 'match',
      confidence: 78,
      matchedProduct: {
        sku: `DH-${sourceProduct.sku}`,
        name: sourceProduct.name,
        price: Math.round(sourceProduct.price * (1 + (Math.random() * 0.3 - 0.1))),
        imageUrl: '/mock/dohome-product.jpg',
        productUrl: competitorUrls?.DOHOME || `https://www.dohome.co.th/p/${sourceProduct.sku}`,
      },
    },
  };

  return competitors.map((competitor) => ({
    competitor,
    status: mockResults[competitor].status || 'error',
    confidence: mockResults[competitor].confidence || 0,
    matchedProduct: mockResults[competitor].matchedProduct,
    errorMessage: mockResults[competitor].errorMessage,
  }));
}

// Generate mock results for V2 flow with multi-URL support
function generateMockResultsV2(
  competitors: CompetitorUrlEntry[],
  thaiWatsadu: ThaiWatsuduInput
): CompetitorMatchResult[] {
  return competitors.map((entry) => {
    const urlResults: UrlComparisonResult[] = entry.urls
      .filter((url) => url.trim() !== '')
      .map((url) => {
        // Randomly determine match status for each URL (weighted towards match)
        const random = Math.random();
        const isMatch = random > 0.3; // 70% chance of match
        const confidence = isMatch
          ? Math.round(75 + Math.random() * 25) // 75-100 for matches
          : Math.round(Math.random() * 40); // 0-40 for non-matches

        return {
          url,
          status: isMatch ? 'match' : 'not_match',
          confidence,
          matchedProduct: isMatch
            ? {
                sku: `${entry.retailer.substring(0, 2)}-${thaiWatsadu.sku}`,
                name: `Product ${thaiWatsadu.sku}`,
                price: Math.round(100 + Math.random() * 5000),
                imageUrl: `/mock/${entry.retailer.toLowerCase()}-product.jpg`,
                productUrl: url,
              }
            : undefined,
        } as UrlComparisonResult;
      });

    // Calculate aggregate counts
    const matchCount = urlResults.filter((r) => r.status === 'match').length;
    const notMatchCount = urlResults.filter((r) => r.status === 'not_match').length;

    // Overall status based on majority
    const overallStatus = matchCount >= notMatchCount ? 'match' : 'not_match';

    // Average confidence for matches, or 0 if none
    const avgConfidence =
      matchCount > 0
        ? Math.round(
            urlResults
              .filter((r) => r.status === 'match')
              .reduce((sum, r) => sum + r.confidence, 0) / matchCount
          )
        : 0;

    return {
      competitor: entry.retailer,
      status: overallStatus,
      confidence: avgConfidence,
      urlResults,
      matchCount,
      notMatchCount,
      matchedProduct:
        matchCount > 0
          ? urlResults.find((r) => r.status === 'match')?.matchedProduct
          : undefined,
    } as CompetitorMatchResult;
  });
}

// Helper to detect if request is V2 format
function isV2Request(body: unknown): body is ManualComparisonRequestV2 {
  const v2 = body as ManualComparisonRequestV2;
  return (
    v2.thaiWatsadu !== undefined &&
    Array.isArray(v2.competitors) &&
    v2.competitors.length > 0 &&
    v2.competitors[0].urls !== undefined
  );
}

// Helper to detect if request is V3 format (Apple-style comparison)
interface AppleStyleComparisonRequest {
  thaiWatsadu: ThaiWatsuduInput;
  competitors: Array<{
    retailer: CompetitorRetailer;
    url: string;
  }>;
}

function isV3Request(body: unknown): body is AppleStyleComparisonRequest {
  const v3 = body as AppleStyleComparisonRequest;
  return (
    v3.thaiWatsadu !== undefined &&
    Array.isArray(v3.competitors) &&
    v3.competitors.length > 0 &&
    v3.competitors[0].url !== undefined &&
    !(v3.competitors[0] as any).urls // Key difference from V2
  );
}

// Generate mock comparison table data for Apple-style comparison
function generateComparisonTableData(
  thaiWatsadu: ThaiWatsuduInput,
  competitors: Array<{ retailer: CompetitorRetailer; url: string }>
): ComparisonTableData {
  // Generate Thai Watsadu product
  const basePrice = Math.round(1000 + Math.random() * 4000);
  const thaiWatsuduProduct: ComparisonTableProduct = {
    sku: thaiWatsadu.sku,
    name: `Product ${thaiWatsadu.sku} - High Quality Item`,
    price: basePrice,
    discountPercentage: Math.random() > 0.5 ? Math.round(5 + Math.random() * 15) : undefined,
    unitPrice: Math.round(basePrice / (1 + Math.random() * 5)),
    imageUrl: '/mock/thaiwatsadu-product.jpg',
    productUrl: thaiWatsadu.url,
    brand: ['SCG', 'TOA', 'MAKITA', 'Generic'][Math.floor(Math.random() * 4)],
    category: ['Building Materials', 'Paint', 'Tools', 'Fixtures'][Math.floor(Math.random() * 4)],
    stockStatus: 'In Stock',
    retailer: 'THAI_WATSADU',
    retailerLogo: '/logos/thaiwatsau.png',
  };

  // Generate competitor products
  const competitorProducts: ComparisonTableProduct[] = competitors.map((comp) => {
    const competitorInfo = COMPETITORS[comp.retailer];
    const priceVariation = 1 + (Math.random() * 0.4 - 0.2); // ±20% variation
    const competitorPrice = Math.round(basePrice * priceVariation);

    return {
      sku: `${comp.retailer.substring(0, 3)}-${thaiWatsadu.sku}`,
      name: thaiWatsuduProduct.name,
      price: competitorPrice,
      discountPercentage: Math.random() > 0.6 ? Math.round(5 + Math.random() * 10) : undefined,
      unitPrice: Math.round(competitorPrice / (1 + Math.random() * 5)),
      imageUrl: `/mock/${comp.retailer.toLowerCase()}-product.jpg`,
      productUrl: comp.url,
      brand: thaiWatsuduProduct.brand,
      category: thaiWatsuduProduct.category,
      stockStatus: Math.random() > 0.1 ? 'In Stock' : 'Limited Stock',
      retailer: comp.retailer,
      retailerLogo: competitorInfo.logo,
    };
  });

  return {
    thaiWatsadu: thaiWatsuduProduct,
    competitors: competitorProducts,
  };
}

// Generate mock source product from Thai Watsadu input
function generateSourceProductFromInput(input: ThaiWatsuduInput): SourceProduct {
  return {
    sku: input.sku,
    name: `Product ${input.sku}`,
    nameTh: `สินค้า ${input.sku}`,
    price: Math.round(100 + Math.random() * 5000),
    imageUrl: '/mock/thaiwatsadu-product.jpg',
    productUrl: input.url,
    category: 'General',
    brand: 'Generic',
  };
}

// Mock function to fetch product info from Thaiwatsadu
function getMockSourceProduct(sku: string): SourceProduct | null {
  // Simulate product lookup
  const mockProducts: Record<string, SourceProduct> = {
    '1145439': {
      sku: '1145439',
      name: 'SPC NARA CREAM 17.78X121.92X0.4 CM.',
      nameTh: 'กระเบื้อง SPC นารา ครีม',
      price: 100,
      imageUrl: '/mock/product-1145439.jpg',
      productUrl: 'https://www.thaiwatsadu.com/th/product/1145439',
      category: 'กระเบื้อง',
      brand: 'XX',
    },
    '2234561': {
      sku: '2234561',
      name: 'TOA SUPER SHIELD WHITE 5L',
      nameTh: 'สีทาบ้าน TOA ซุปเปอร์ชิลด์ ขาว 5 ลิตร',
      price: 850,
      imageUrl: '/mock/product-2234561.jpg',
      productUrl: 'https://www.thaiwatsadu.com/th/product/2234561',
      category: 'สีทาบ้าน',
      brand: 'TOA',
    },
    '3345672': {
      sku: '3345672',
      name: 'MAKITA HAMMER DRILL HP1641',
      nameTh: 'สว่านกระแทก มากีต้า HP1641',
      price: 2450,
      imageUrl: '/mock/product-3345672.jpg',
      productUrl: 'https://www.thaiwatsadu.com/th/product/3345672',
      category: 'เครื่องมือช่าง',
      brand: 'MAKITA',
    },
  };

  // Return mock product or generate one for unknown SKUs
  if (mockProducts[sku]) {
    return mockProducts[sku];
  }

  // Generate a generic product for any SKU
  return {
    sku,
    name: `Product ${sku}`,
    nameTh: `สินค้า ${sku}`,
    price: Math.round(100 + Math.random() * 5000),
    imageUrl: '/mock/generic-product.jpg',
    productUrl: `https://www.thaiwatsadu.com/th/product/${sku}`,
    category: 'General',
    brand: 'Generic',
  };
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Check if this is a V3 request (Apple-style comparison)
    if (isV3Request(body)) {
      const v3Body = body as AppleStyleComparisonRequest;

      // Validate V3 request
      if (!v3Body.thaiWatsadu.sku || !v3Body.thaiWatsadu.url) {
        return NextResponse.json(
          { error: 'Thai Watsadu SKU and URL are required' },
          { status: 400 }
        );
      }

      if (!v3Body.competitors || v3Body.competitors.length === 0) {
        return NextResponse.json(
          { error: 'At least one competitor must be selected' },
          { status: 400 }
        );
      }

      // Simulate processing delay
      await new Promise((resolve) => setTimeout(resolve, 1500));

      // Generate comparison table data
      const comparisonData = generateComparisonTableData(
        v3Body.thaiWatsadu,
        v3Body.competitors
      );

      return NextResponse.json(comparisonData);
    }

    // Check if this is a V2 request
    if (isV2Request(body)) {
      // V2 Flow: Thai Watsadu input + competitor URLs
      const v2Body = body as ManualComparisonRequestV2;

      // Validate V2 request
      if (!v2Body.thaiWatsadu.sku || !v2Body.thaiWatsadu.url) {
        return NextResponse.json(
          { error: 'Thai Watsadu SKU and URL are required' },
          { status: 400 }
        );
      }

      if (!v2Body.competitors || v2Body.competitors.length === 0) {
        return NextResponse.json(
          { error: 'At least one competitor must be selected' },
          { status: 400 }
        );
      }

      // Simulate processing delay
      await new Promise((resolve) => setTimeout(resolve, 1500));

      // Generate source product from Thai Watsadu input
      const sourceProduct = generateSourceProductFromInput(v2Body.thaiWatsadu);

      // Generate mock results for V2 flow
      const results = generateMockResultsV2(v2Body.competitors, v2Body.thaiWatsadu);

      const response: ManualComparisonResponse = {
        id: generateComparisonId(),
        sourceProduct,
        results,
        createdAt: new Date().toISOString(),
      };

      return NextResponse.json(response);
    }

    // Legacy V1 Flow
    const v1Body = body as ManualComparisonRequest;

    // Validate request
    if (!v1Body.sourceProduct) {
      return NextResponse.json(
        { error: 'Source product is required' },
        { status: 400 }
      );
    }

    if (!v1Body.competitors || v1Body.competitors.length === 0) {
      return NextResponse.json(
        { error: 'At least one competitor must be selected' },
        { status: 400 }
      );
    }

    // Simulate processing delay
    await new Promise((resolve) => setTimeout(resolve, 1500));

    // Generate mock results
    const results = generateMockResults(
      v1Body.competitors,
      v1Body.sourceProduct,
      v1Body.competitorUrls
    );

    const response: ManualComparisonResponse = {
      id: generateComparisonId(),
      sourceProduct: v1Body.sourceProduct,
      results,
      createdAt: new Date().toISOString(),
    };

    return NextResponse.json(response);
  } catch (error) {
    console.error('Error processing comparison:', error);
    return NextResponse.json(
      { error: 'Failed to process comparison' },
      { status: 500 }
    );
  }
}

// GET endpoint to fetch product info by SKU
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const sku = searchParams.get('sku');
  const url = searchParams.get('url');

  if (!sku && !url) {
    return NextResponse.json(
      { error: 'SKU or URL parameter is required' },
      { status: 400 }
    );
  }

  // Simulate processing delay
  await new Promise((resolve) => setTimeout(resolve, 500));

  let productSku = sku;

  // Extract SKU from URL if URL is provided
  if (url && !sku) {
    try {
      const urlObj = new URL(url);
      const pathParts = urlObj.pathname.split('/').filter(Boolean);
      productSku = pathParts[pathParts.length - 1] || null;
    } catch {
      return NextResponse.json(
        { error: 'Invalid URL format' },
        { status: 400 }
      );
    }
  }

  if (!productSku) {
    return NextResponse.json(
      { error: 'Could not extract SKU from URL' },
      { status: 400 }
    );
  }

  const product = getMockSourceProduct(productSku);

  if (!product) {
    return NextResponse.json(
      { error: 'Product not found' },
      { status: 404 }
    );
  }

  return NextResponse.json({ product });
}
