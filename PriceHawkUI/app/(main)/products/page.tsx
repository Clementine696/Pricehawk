'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { MainLayout } from '@/components/layout/MainLayout';
import { ProductSearchFilter } from '@/components/products/ProductSearchFilter';
import { PriceComparisonTable } from '@/components/products/PriceComparisonTable';
import {
  ProductComparison,
  ProductComparisonListResponse,
  ProductFilterState,
  ValidationStatus,
} from '@/lib/types/price-comparison';
import { exportToCSV } from '@/lib/utils/export-utils';
import { getAllValidationStatusesForAllProducts } from '@/lib/utils/validation-storage';
import { getAllManualComparisonProducts } from '@/lib/utils/manual-comparison-storage';

export default function ProductsPage() {
  const router = useRouter();
  const [data, setData] = useState<ProductComparisonListResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [filters, setFilters] = useState<ProductFilterState>({
    search: '',
    category: null,
    brand: null,
    status: null,
    sortBy: 'name',
    sortOrder: 'asc',
  });
  const [page, setPage] = useState(1);
  const pageSize = 10;
  const [validationStatuses, setValidationStatuses] = useState<Record<string, Record<string, ValidationStatus>>>({});

  // Load validation statuses from localStorage on mount
  useEffect(() => {
    const statuses = getAllValidationStatusesForAllProducts();
    setValidationStatuses(statuses);
  }, []);

  // Fetch products data
  useEffect(() => {
    const fetchProducts = async () => {
      setIsLoading(true);
      try {
        const params = new URLSearchParams({
          page: page.toString(),
          pageSize: pageSize.toString(),
          ...(filters.search && { search: filters.search }),
          ...(filters.category && { category: filters.category }),
          ...(filters.brand && { brand: filters.brand }),
          ...(filters.status && { status: filters.status }),
          sortBy: filters.sortBy,
          sortOrder: filters.sortOrder,
        });

        const response = await fetch(`/api/products/comparison?${params}`);
        if (!response.ok) throw new Error('Failed to fetch products');

        const result: ProductComparisonListResponse = await response.json();

        // Get manual products from localStorage
        const manualProducts = getAllManualComparisonProducts();

        // Merge manual products with API products
        // Manual products appear first (most recent)
        const mergedProducts = [...manualProducts, ...result.products];

        // Apply filters to merged dataset
        let filteredProducts = mergedProducts;

        // Apply search filter
        if (filters.search) {
          const searchLower = filters.search.toLowerCase();
          filteredProducts = filteredProducts.filter(
            (p) =>
              p.name.toLowerCase().includes(searchLower) ||
              p.sku.toLowerCase().includes(searchLower) ||
              p.brand.toLowerCase().includes(searchLower) ||
              p.category.toLowerCase().includes(searchLower)
          );
        }

        // Apply category filter
        if (filters.category) {
          filteredProducts = filteredProducts.filter(
            (p) => p.category === filters.category || p.categoryTh === filters.category
          );
        }

        // Apply brand filter
        if (filters.brand) {
          filteredProducts = filteredProducts.filter((p) => p.brand === filters.brand);
        }

        // Apply status filter
        if (filters.status) {
          filteredProducts = filteredProducts.filter((p) => p.status === filters.status);
        }

        // Apply sorting
        filteredProducts.sort((a, b) => {
          let aValue: any;
          let bValue: any;

          switch (filters.sortBy) {
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

          if (aValue < bValue) return filters.sortOrder === 'asc' ? -1 : 1;
          if (aValue > bValue) return filters.sortOrder === 'asc' ? 1 : -1;
          return 0;
        });

        // Calculate new pagination
        const total = filteredProducts.length;
        const totalPages = Math.ceil(total / pageSize);
        const startIndex = (page - 1) * pageSize;
        const endIndex = startIndex + pageSize;
        const paginatedProducts = filteredProducts.slice(startIndex, endIndex);

        // Update filters to include manual products
        const allMergedProducts = [...manualProducts, ...result.products];
        const categories = Array.from(
          new Set(allMergedProducts.map((p) => p.categoryTh || p.category))
        ).map((cat) => ({
          value: cat,
          label: cat,
          count: allMergedProducts.filter((p) => (p.categoryTh || p.category) === cat).length,
        }));

        const brands = Array.from(new Set(allMergedProducts.map((p) => p.brand))).map((brand) => ({
          value: brand,
          label: brand,
          count: allMergedProducts.filter((p) => p.brand === brand).length,
        }));

        // Update result with merged data
        const updatedResult: ProductComparisonListResponse = {
          ...result,
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
          summary: {
            totalProducts: allMergedProducts.length,
            cheapestCount: allMergedProducts.filter((p) => p.status === 'cheapest').length,
            higherCount: allMergedProducts.filter((p) => p.status === 'higher').length,
            sameCount: allMergedProducts.filter((p) => p.status === 'same').length,
            unavailableCount: allMergedProducts.filter((p) => p.status === 'unavailable').length,
          },
        };

        setData(updatedResult);
      } catch (error) {
        console.error('Error fetching products:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchProducts();
  }, [filters, page]);

  const handleFilterChange = (newFilters: Partial<ProductFilterState>) => {
    setFilters((prev) => ({ ...prev, ...newFilters }));
    setPage(1); // Reset to first page when filters change
  };

  const handleReset = () => {
    setFilters({
      search: '',
      category: null,
      brand: null,
      status: null,
      sortBy: 'name',
      sortOrder: 'asc',
    });
    setPage(1);
  };

  const handleExport = () => {
    if (data?.products) {
      exportToCSV(data.products);
    }
  };

  const handleRowClick = (product: ProductComparison) => {
    router.push(`/products/${product.id}`);
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Products</h1>
          <p className="text-gray-600 mt-1">Compare prices across retailers</p>
        </div>

        {/* Search & Filter */}
        <ProductSearchFilter
          filters={filters}
          categories={data?.filters.categories || []}
          brands={data?.filters.brands || []}
          onFilterChange={handleFilterChange}
          onReset={handleReset}
          onExport={handleExport}
        />

        {/* Price Comparison Section */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Price Comparison
          </h2>

          {/* Table */}
          <PriceComparisonTable
            products={data?.products || []}
            isLoading={isLoading}
            onRowClick={handleRowClick}
            sortBy={filters.sortBy}
            sortOrder={filters.sortOrder}
            validationStatuses={validationStatuses}
          />

          {/* Pagination Info */}
          {data && !isLoading && (
            <div className="flex justify-between items-center">
              <p className="text-sm text-gray-600">
                Showing {data.products.length === 0 ? 0 : (page - 1) * pageSize + 1} to{' '}
                {Math.min(page * pageSize, data.pagination.total)} of{' '}
                {data.pagination.total} products
              </p>

              {/* Pagination Controls */}
              {data.pagination.totalPages > 1 && (
                <div className="flex gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-3 py-1 border rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                  >
                    Previous
                  </button>
                  <span className="px-3 py-1 text-sm">
                    Page {page} of {data.pagination.totalPages}
                  </span>
                  <button
                    onClick={() =>
                      setPage((p) => Math.min(data.pagination.totalPages, p + 1))
                    }
                    disabled={page === data.pagination.totalPages}
                    className="px-3 py-1 border rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                  >
                    Next
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </MainLayout>
  );
}
