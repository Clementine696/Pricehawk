import { NextRequest, NextResponse } from 'next/server';
import mockData from '@/data/mock-products.json';
import { ProductComparison, ProductComparisonListResponse } from '@/lib/types/price-comparison';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;

    // Extract query parameters
    const search = searchParams.get('search') || '';
    const category = searchParams.get('category');
    const brand = searchParams.get('brand');
    const status = searchParams.get('status');
    const page = parseInt(searchParams.get('page') || '1', 10);
    const pageSize = parseInt(searchParams.get('pageSize') || '10', 10);
    const sortBy = searchParams.get('sortBy') || 'name';
    const sortOrder = searchParams.get('sortOrder') || 'asc';

    let products: ProductComparison[] = mockData.products as ProductComparison[];

    // Apply search filter
    if (search) {
      const searchLower = search.toLowerCase();
      products = products.filter(
        (p) =>
          p.name.toLowerCase().includes(searchLower) ||
          p.sku.toLowerCase().includes(searchLower) ||
          p.brand.toLowerCase().includes(searchLower) ||
          p.category.toLowerCase().includes(searchLower)
      );
    }

    // Apply category filter
    if (category) {
      products = products.filter((p) => p.category === category || p.categoryTh === category);
    }

    // Apply brand filter
    if (brand) {
      products = products.filter((p) => p.brand === brand);
    }

    // Apply status filter
    if (status) {
      products = products.filter((p) => p.status === status);
    }

    // Apply sorting
    products.sort((a, b) => {
      let aValue: any;
      let bValue: any;

      switch (sortBy) {
        case 'name':
          aValue = a.name.toLowerCase();
          bValue = b.name.toLowerCase();
          break;
        case 'sku':
          aValue = a.sku;
          bValue = b.sku;
          break;
        case 'category':
          aValue = a.category.toLowerCase();
          bValue = b.category.toLowerCase();
          break;
        case 'brand':
          aValue = a.brand.toLowerCase();
          bValue = b.brand.toLowerCase();
          break;
        case 'price':
          aValue = a.prices.thai_watsadu.price || 0;
          bValue = b.prices.thai_watsadu.price || 0;
          break;
        case 'status':
          aValue = a.status;
          bValue = b.status;
          break;
        default:
          aValue = a.name.toLowerCase();
          bValue = b.name.toLowerCase();
      }

      if (aValue < bValue) return sortOrder === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });

    // Calculate pagination
    const total = products.length;
    const totalPages = Math.ceil(total / pageSize);
    const startIndex = (page - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    const paginatedProducts = products.slice(startIndex, endIndex);

    // Calculate available filters
    const allProducts = mockData.products as ProductComparison[];
    const categories = Array.from(
      new Set(allProducts.map((p) => p.categoryTh || p.category))
    ).map((cat) => ({
      value: cat,
      label: cat,
      count: allProducts.filter((p) => (p.categoryTh || p.category) === cat).length,
    }));

    const brands = Array.from(new Set(allProducts.map((p) => p.brand))).map((brand) => ({
      value: brand,
      label: brand,
      count: allProducts.filter((p) => p.brand === brand).length,
    }));

    // Calculate summary statistics
    const summary = {
      totalProducts: allProducts.length,
      cheapestCount: allProducts.filter((p) => p.status === 'cheapest').length,
      higherCount: allProducts.filter((p) => p.status === 'higher').length,
      sameCount: allProducts.filter((p) => p.status === 'same').length,
      unavailableCount: allProducts.filter((p) => p.status === 'unavailable').length,
    };

    const response: ProductComparisonListResponse = {
      products: paginatedProducts,
      pagination: {
        page,
        pageSize,
        total,
        totalPages,
      },
      filters: {
        categories,
        brands,
      },
      summary,
    };

    return NextResponse.json(response);
  } catch (error) {
    console.error('Error in /api/products/comparison:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
