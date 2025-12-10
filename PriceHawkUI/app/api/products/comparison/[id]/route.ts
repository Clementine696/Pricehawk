import { NextRequest, NextResponse } from 'next/server';
import mockData from '@/data/mock-products.json';
import { ProductComparison, ProductComparisonDetailResponse, Retailer } from '@/lib/types/price-comparison';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;

    // Check if this is a manual product ID
    if (id.startsWith('manual_')) {
      // Signal to client to load from localStorage
      return NextResponse.json({
        isManual: true,
        message: 'Manual product - load from client storage'
      });
    }

    const allProducts = mockData.products as ProductComparison[];
    const product = allProducts.find((p) => p.id === id);

    if (!product) {
      return NextResponse.json(
        { error: 'Product not found' },
        { status: 404 }
      );
    }

    // Mock price history data (last 7 days)
    const priceHistory = Array.from({ length: 7 }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - (6 - i));

      return {
        date: date.toISOString(),
        prices: {
          [Retailer.THAI_WATSADU]: product.prices[Retailer.THAI_WATSADU].price,
          [Retailer.HOMEPRO]: product.prices[Retailer.HOMEPRO].price,
          [Retailer.GLOBAL_HOUSE]: product.prices[Retailer.GLOBAL_HOUSE].price,
          [Retailer.DOHOME]: product.prices[Retailer.DOHOME].price,
          [Retailer.BOONTHAVORN]: product.prices[Retailer.BOONTHAVORN].price,
        },
      };
    });

    // Mock matched products data with varied confidence and match types
    const matchedProducts = Object.values(Retailer)
      .filter((retailer) => retailer !== Retailer.THAI_WATSADU)
      .filter((retailer) => product.prices[retailer].price !== null)
      .map((retailer, index) => {
        // Vary confidence and match type for demonstration
        // First retailer gets exact match with high confidence
        // Others get varied values to show the UI capabilities
        const isExact = index < 2;
        const confidence = isExact
          ? 95 + Math.floor(Math.random() * 6) // 95-100% for exact
          : 80 + Math.floor(Math.random() * 15); // 80-94% for similar

        return {
          retailer,
          confidence,
          matchType: isExact ? ('exact' as const) : ('similar' as const),
          products: [{
            id: `${retailer}_${product.sku}`,
            name: product.name,
            sku: product.sku,
            imageUrl: product.imageUrl,
            price: product.prices[retailer].price || 0,
            url: product.prices[retailer].productUrl || '',
            description: product.description,
            brand: product.brand,
            category: product.category,
          }],
        };
      });

    const response: ProductComparisonDetailResponse = {
      product,
      priceHistory,
      matchedProducts,
    };

    return NextResponse.json(response);
  } catch (error) {
    console.error('Error in /api/products/comparison/[id]:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
