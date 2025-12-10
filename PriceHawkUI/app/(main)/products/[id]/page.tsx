'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { MainLayout } from '@/components/layout/MainLayout';
import { ProductDetailCard } from '@/components/products/ProductDetailCard';
import { MatchedProductCard } from '@/components/products/MatchedProductCard';
import { ManualComparisonButton } from '@/components/products/ManualComparisonButton';
import {
  ProductComparisonDetailResponse,
  RetailerMatch,
  ValidationStatus,
  LegacyMatchedProduct,
  Retailer,
} from '@/lib/types/price-comparison';
import {
  getAllValidationStatuses,
  setValidationStatus,
  getManualComparison,
  clearValidationStatuses,
  ManualComparisonData,
} from '@/lib/utils/validation-storage';
import {
  getManualComparisonProductById,
  isManualProductId,
} from '@/lib/utils/manual-comparison-storage';
import { RotateCcw } from 'lucide-react';

// Transform legacy API response to new multi-product format
function transformMatchedProducts(
  matchedProducts: LegacyMatchedProduct[] | RetailerMatch[],
  validationStatuses: Record<string, ValidationStatus>
): RetailerMatch[] {
  return matchedProducts.map((match) => {
    // Check if it's already in new format (has 'products' array)
    if ('products' in match && Array.isArray(match.products)) {
      return {
        ...match,
        products: match.products.map((product) => ({
          ...product,
          validationStatus: validationStatuses[product.id] || product.validationStatus,
        })),
      };
    }

    // Transform legacy format (has 'product' object) to new format
    const legacyMatch = match as LegacyMatchedProduct;
    const productId = `${legacyMatch.retailer}_${legacyMatch.product.sku}`;
    return {
      retailer: legacyMatch.retailer,
      confidence: legacyMatch.confidence,
      matchType: legacyMatch.matchType,
      products: [
        {
          id: productId,
          name: legacyMatch.product.name,
          sku: legacyMatch.product.sku,
          imageUrl: legacyMatch.product.imageUrl,
          price: legacyMatch.product.price,
          url: legacyMatch.product.url,
          description: legacyMatch.product.description,
          brand: legacyMatch.product.brand,
          category: legacyMatch.product.category,
          validationStatus: validationStatuses[productId],
        },
      ],
    };
  });
}

// Filter out products marked as incorrect
function filterIncorrectProducts(matchedProducts: RetailerMatch[]): RetailerMatch[] {
  return matchedProducts
    .map((match) => ({
      ...match,
      products: match.products.filter(
        (product) => product.validationStatus !== 'incorrect'
      ),
    }))
    .filter((match) => match.products.length > 0);
}

// Check if all products are marked as incorrect
function areAllProductsIncorrect(
  matchedProducts: RetailerMatch[],
  validationStatuses: Record<string, ValidationStatus>
): boolean {
  const allProductIds = matchedProducts.flatMap((match) =>
    match.products.map((product) => product.id)
  );

  if (allProductIds.length === 0) return true;

  return allProductIds.every(
    (id) => validationStatuses[id] === 'incorrect'
  );
}

export default function ProductDetailPage() {
  const params = useParams();
  const router = useRouter();
  const productId = params.id as string;

  const [data, setData] = useState<ProductComparisonDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [validationStatuses, setValidationStatuses] = useState<Record<string, ValidationStatus>>({});
  const [showManualForm, setShowManualForm] = useState(false);
  const [manualComparisonData, setManualComparisonData] = useState<ManualComparisonData | null>(null);

  // Load validation statuses and manual comparison from localStorage on mount
  useEffect(() => {
    if (productId) {
      const statuses = getAllValidationStatuses(productId);
      setValidationStatuses(statuses);
      const manualData = getManualComparison(productId);
      setManualComparisonData(manualData);
    }
  }, [productId]);

  // Fetch product detail
  useEffect(() => {
    const fetchProductDetail = async () => {
      setIsLoading(true);
      setError(null);
      try {
        // Check if this is a manual product
        if (isManualProductId(productId)) {
          const manualProduct = getManualComparisonProductById(productId);

          if (!manualProduct) {
            throw new Error('Manual product not found');
          }

          // Generate price history (mock data for manual products)
          const priceHistory = Array.from({ length: 7 }, (_, i) => {
            const date = new Date();
            date.setDate(date.getDate() - (6 - i));

            return {
              date: date.toISOString(),
              prices: {
                [Retailer.THAI_WATSADU]: manualProduct.prices[Retailer.THAI_WATSADU].price,
                [Retailer.HOMEPRO]: manualProduct.prices[Retailer.HOMEPRO].price,
                [Retailer.GLOBAL_HOUSE]: manualProduct.prices[Retailer.GLOBAL_HOUSE].price,
                [Retailer.DOHOME]: manualProduct.prices[Retailer.DOHOME].price,
                [Retailer.BOONTHAVORN]: manualProduct.prices[Retailer.BOONTHAVORN].price,
              },
            };
          });

          // Generate matched products from manual product prices
          const matchedProducts = Object.values(Retailer)
            .filter((retailer) => retailer !== Retailer.THAI_WATSADU)
            .filter((retailer) => manualProduct.prices[retailer].price !== null)
            .map((retailer): RetailerMatch => {
              const retailerPrice = manualProduct.prices[retailer];
              return {
                retailer,
                confidence: 100, // Manual entries are 100% confident
                matchType: 'exact',
                products: [{
                  id: `${retailer}_${manualProduct.sku}`,
                  name: manualProduct.name,
                  sku: manualProduct.sku,
                  imageUrl: manualProduct.imageUrl,
                  price: retailerPrice.price || 0,
                  url: retailerPrice.productUrl || '',
                  description: manualProduct.description,
                  brand: manualProduct.brand,
                  category: manualProduct.category,
                  isManualEntry: true,
                }],
              };
            });

          const result: ProductComparisonDetailResponse = {
            product: manualProduct,
            priceHistory,
            matchedProducts,
          };

          setData(result);
          setIsLoading(false);
          return;
        }

        // Regular API fetch for non-manual products
        const response = await fetch(`/api/products/comparison/${productId}`);
        if (!response.ok) {
          if (response.status === 404) {
            throw new Error('Product not found');
          }
          throw new Error('Failed to fetch product details');
        }
        const result: ProductComparisonDetailResponse = await response.json();
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setIsLoading(false);
      }
    };

    if (productId) {
      fetchProductDetail();
    }
  }, [productId]);

  // Handle marking product as correct
  const handleMarkCorrect = useCallback((matchedProductId: string) => {
    setValidationStatus(productId, matchedProductId, 'correct');
    setValidationStatuses((prev) => ({
      ...prev,
      [matchedProductId]: 'correct',
    }));
  }, [productId]);

  // Handle marking product as incorrect
  const handleMarkIncorrect = useCallback((matchedProductId: string) => {
    setValidationStatus(productId, matchedProductId, 'incorrect');
    setValidationStatuses((prev) => ({
      ...prev,
      [matchedProductId]: 'incorrect',
    }));
  }, [productId]);

  // Handle reset validations
  const handleResetValidations = useCallback(() => {
    clearValidationStatuses(productId);
    setValidationStatuses({});
    setShowManualForm(false);
  }, [productId]);

  // Transform and filter matched products
  const transformedMatchedProducts = data
    ? transformMatchedProducts(
        data.matchedProducts as (LegacyMatchedProduct[] | RetailerMatch[]),
        validationStatuses
      )
    : [];

  const filteredMatchedProducts = filterIncorrectProducts(transformedMatchedProducts);

  // Check if we should show manual form
  const shouldShowManualForm =
    showManualForm ||
    (transformedMatchedProducts.length > 0 &&
      areAllProductsIncorrect(transformedMatchedProducts, validationStatuses));

  // Count total and filtered products
  const totalProducts = transformedMatchedProducts.reduce(
    (sum, match) => sum + match.products.length,
    0
  );
  const visibleProducts = filteredMatchedProducts.reduce(
    (sum, match) => sum + match.products.length,
    0
  );
  const hasHiddenProducts = totalProducts > visibleProducts;

  // Loading state
  if (isLoading) {
    return (
      <MainLayout>
        <div className="space-y-6">
          {/* Breadcrumb skeleton */}
          <div className="h-6 w-48 bg-gray-200 rounded animate-pulse" />

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left panel skeleton */}
            <div className="lg:col-span-5">
              <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-4">
                <div className="h-8 w-32 bg-gray-200 rounded animate-pulse" />
                <div className="aspect-square bg-gray-200 rounded animate-pulse" />
                <div className="space-y-2">
                  <div className="h-6 bg-gray-200 rounded animate-pulse" />
                  <div className="h-4 w-3/4 bg-gray-200 rounded animate-pulse" />
                </div>
              </div>
            </div>

            {/* Right panel skeleton */}
            <div className="lg:col-span-7 space-y-4">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="bg-white rounded-lg border border-gray-200 p-4 h-40 animate-pulse"
                >
                  <div className="h-4 w-24 bg-gray-200 rounded mb-4" />
                  <div className="flex gap-4">
                    <div className="w-24 h-24 bg-gray-200 rounded" />
                    <div className="flex-1 space-y-2">
                      <div className="h-4 bg-gray-200 rounded" />
                      <div className="h-3 w-1/2 bg-gray-200 rounded" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </MainLayout>
    );
  }

  // Error state
  if (error) {
    return (
      <MainLayout>
        <div className="space-y-6">
          {/* Breadcrumb */}
          <nav className="flex items-center gap-2 text-sm text-gray-500">
            <Link href="/products" className="hover:text-gray-700">
              Products
            </Link>
            <span>/</span>
            <span className="text-gray-900">Error</span>
          </nav>

          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <svg
              className="w-12 h-12 mx-auto text-red-400 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <h2 className="text-lg font-semibold text-red-800 mb-2">
              {error}
            </h2>
            <p className="text-red-600 mb-4">
              Unable to load product details. Please try again.
            </p>
            <div className="flex justify-center gap-4">
              <button
                onClick={() => router.back()}
                className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
              >
                Go Back
              </button>
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Retry
              </button>
            </div>
          </div>
        </div>
      </MainLayout>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Breadcrumb & Back Button */}
        <div className="flex items-center justify-between">
          <nav className="flex items-center gap-2 text-sm text-gray-500">
            <Link
              href="/products"
              className="hover:text-gray-700 flex items-center gap-1"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 19l-7-7 7-7"
                />
              </svg>
              Products
            </Link>
            <span>/</span>
            <span className="text-gray-900 font-medium truncate max-w-xs">
              {data.product.name}
            </span>
          </nav>

          <button
            onClick={() => router.back()}
            className="px-4 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 flex items-center gap-2"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10 19l-7-7m0 0l7-7m-7 7h18"
              />
            </svg>
            Back to List
          </button>
        </div>

        {/* Page Title */}
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900">
              Product Comparison Detail
            </h1>
            {isManualProductId(productId) && (
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold bg-purple-100 text-purple-800">
                Manual Entry
              </span>
            )}
          </div>
          <p className="text-gray-600 mt-1">
            Compare prices and verify product matches across retailers
          </p>
        </div>

        {/* Main Content - Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Panel - Thai Watsadu Product (Primary) - 40% width */}
          <div className="lg:col-span-5">
            <ProductDetailCard product={data.product} />
          </div>

          {/* Right Panel - Matched Products - 60% width */}
          <div className="lg:col-span-7 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">
                Matched Products
              </h2>
              <div className="flex items-center gap-3">
                {hasHiddenProducts && (
                  <button
                    onClick={handleResetValidations}
                    className="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    <RotateCcw className="w-4 h-4" />
                    Reset
                  </button>
                )}
                <span className="text-sm text-gray-500">
                  {visibleProducts} of {totalProducts} matches shown
                </span>
              </div>
            </div>

            {/* Manual Comparison Button - Show when all products are incorrect */}
            {shouldShowManualForm && (
              <div className="mb-4">
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                  <p className="text-sm text-yellow-800">
                    All matched products have been marked as incorrect. Click the button below to manually compare this product.
                  </p>
                </div>
                <ManualComparisonButton
                  productId={productId}
                  sku={data.product.sku}
                  url={data.product.prices[Retailer.THAI_WATSADU]?.productUrl}
                />
              </div>
            )}

            {/* Manual Comparison Data Display */}
            {manualComparisonData && !shouldShowManualForm && (
              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-purple-800">
                    Manual Comparison Entry
                  </span>
                  <span className="text-xs text-purple-600">
                    Added {new Date(manualComparisonData.createdAt).toLocaleDateString()}
                  </span>
                </div>
                <div className="text-sm text-purple-700">
                  <p><strong>Product:</strong> {manualComparisonData.productName}</p>
                  <p><strong>SKU:</strong> {manualComparisonData.sku}</p>
                  <p><strong>Price:</strong> ฿{manualComparisonData.price.toLocaleString()}</p>
                </div>
              </div>
            )}

            {filteredMatchedProducts.length > 0 ? (
              <div className="space-y-4">
                {filteredMatchedProducts.map((match) => (
                  <MatchedProductCard
                    key={match.retailer}
                    retailer={match.retailer}
                    confidence={match.confidence}
                    matchType={match.matchType}
                    products={match.products}
                    onMarkCorrect={handleMarkCorrect}
                    onMarkIncorrect={handleMarkIncorrect}
                  />
                ))}
              </div>
            ) : !shouldShowManualForm ? (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
                <svg
                  className="w-12 h-12 mx-auto text-gray-400 mb-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <p className="text-gray-600">
                  No matched products found from other retailers.
                </p>
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </MainLayout>
  );
}
