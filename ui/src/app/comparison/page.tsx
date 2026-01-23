'use client';

import React, { useState, useEffect } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Search, Check, X, AlertCircle } from 'lucide-react';
import { apiFetch } from '@/lib/api';

interface Match {
  match_id: number;
  is_same: boolean | null;
  confidence_score: number | null;
  reason: string | null;
  match_type: string;
  verified_by_user: boolean;
  candidate_product: {
    product_id: number;
    name: string;
    sku: string;
    retailer_name: string;
    current_price: number | null;
    image: string | null;
  };
}

interface RetailerMatches {
  retailer_name: string;
  retailer_id: number;
  matches: Match[];
}

interface ProductGroup {
  base_product: {
    product_id: number;
    name: string;
    sku: string;
    retailer_name: string;
    retailer_id: number;
    current_price: number | null;
    image: string | null;
  };
  matches_by_retailer: RetailerMatches[];
}

export default function ComparisonPage() {
  const [products, setProducts] = useState<ProductGroup[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [allRetailers, setAllRetailers] = useState<string[]>([]);
  const [displayCount, setDisplayCount] = useState(10); // Initially show 10 products
  const [isLoadingMore, setIsLoadingMore] = useState(false);

  useEffect(() => {
    fetchMatches();
  }, []);

  useEffect(() => {
    const handleScroll = () => {
      // Check if we should load more
      if (isLoadingMore || isLoading) return;

      const scrollHeight = document.documentElement.scrollHeight;
      const scrollTop = document.documentElement.scrollTop;
      const clientHeight = document.documentElement.clientHeight;

      // Load more when user scrolls near bottom (within 300px)
      if (scrollHeight - scrollTop - clientHeight < 300) {
        loadMore();
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [isLoadingMore, isLoading, displayCount]);

  const fetchMatches = async () => {
    setIsLoading(true);
    try {
      const response = await apiFetch('/api/matches/grouped');
      if (!response.ok) throw new Error('Failed to fetch matches');
      const data = await response.json();
      setProducts(data.products || []);
      
      // Get unique retailers (excluding Thai Watsadu)
      const retailerSet = new Set<string>();
      data.products?.forEach((p: ProductGroup) => {
        p.matches_by_retailer.forEach((r) => {
          if (r.retailer_name !== 'Thai Watsadu') {
            retailerSet.add(r.retailer_name);
          }
        });
      });
      setAllRetailers(Array.from(retailerSet).sort());
    } catch (error) {
      console.error('Error fetching matches:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerify = async (matchId: number, isSame: boolean) => {
    try {
      const response = await apiFetch(`/api/matches/${matchId}/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_same: isSame }),
      });

      if (!response.ok) throw new Error('Failed to verify match');

      // Update local state
      setProducts((prev) =>
        prev.map((product) => ({
          ...product,
          matches_by_retailer: product.matches_by_retailer.map((retailer) => ({
            ...retailer,
            matches: retailer.matches.map((m) =>
              m.match_id === matchId
                ? { ...m, verified_by_user: true, is_same: isSame }
                : m
            ),
          })),
        }))
      );
    } catch (error) {
      console.error('Error verifying match:', error);
    }
  };

  const loadMore = () => {
    setIsLoadingMore(true);
    // Simulate loading delay
    setTimeout(() => {
      setDisplayCount((prev) => prev + 10); // Load 10 more products
      setIsLoadingMore(false);
    }, 300);
  };

  const filteredProducts = products
    .filter((product) =>
      product.base_product.name?.toLowerCase().includes(searchTerm.toLowerCase())
    )
    .map((product) => {
      // Filter to only show retailers with unverified matches
      const unverifiedRetailers = product.matches_by_retailer
        .map((retailer) => ({
          ...retailer,
          matches: retailer.matches.filter((m) => !m.verified_by_user),
        }))
        .filter((retailer) => retailer.matches.length > 0);

      return {
        ...product,
        matches_by_retailer: unverifiedRetailers,
      };
    })
    .filter((product) => product.matches_by_retailer.length > 0);

  // Slice to show only displayCount products
  const displayedProducts = filteredProducts.slice(0, displayCount);
  const hasMore = displayCount < filteredProducts.length;

  const getTotalMatches = () => {
    return filteredProducts.reduce(
      (sum, p) =>
        sum + p.matches_by_retailer.reduce((s, r) => s + r.matches.length, 0),
      0
    );
  };

  const formatPrice = (price: number | null) => {
    if (price === null) return '-';
    return new Intl.NumberFormat('th-TH', {
      style: 'currency',
      currency: 'THB',
      minimumFractionDigits: 0,
    }).format(price);
  };

  const getConfidenceColor = (score: number | null) => {
    if (score === null) return 'text-gray-500';
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.5) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Product Comparison</h1>
          <p className="text-gray-600 mt-1">Review and verify product matches across retailers</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-2xl font-bold text-gray-900">{filteredProducts.length}</div>
            <div className="text-sm text-gray-500">Products Pending Review</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-2xl font-bold text-orange-600">
              {getTotalMatches()}
            </div>
            <div className="text-sm text-gray-500">Total Unverified Matches</div>
          </div>
        </div>

        {/* Search */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Search products..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* Comparison Table */}
        <div className="space-y-4">
          {isLoading ? (
            <div className="bg-white rounded-lg shadow p-12 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-500 mx-auto"></div>
              <p className="mt-2 text-gray-500">Loading matches...</p>
            </div>
          ) : filteredProducts.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-12 text-center">
              <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">No products pending review</p>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider sticky left-0 bg-gray-50 z-10 min-w-[250px]">
                      Thai Watsadu
                    </th>
                    {allRetailers.map((retailer) => (
                      <th
                        key={retailer}
                        className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider min-w-[250px]"
                      >
                        {retailer}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {displayedProducts.map((product) => {
                    // Create a map of retailer matches for easy lookup
                    const retailerMatchesMap = new Map(
                      product.matches_by_retailer.map((r) => [r.retailer_name, r.matches])
                    );

                    return (
                      <tr key={product.base_product.product_id} className="hover:bg-gray-50">
                        {/* Thai Watsadu Column - Sticky */}
                        <td className="px-4 py-4 sticky left-0 bg-white z-10 border-r border-gray-200">
                          <div className="flex items-start gap-3">
                            <div className="w-16 h-16 flex-shrink-0">
                              {product.base_product.image ? (
                                <img
                                  src={product.base_product.image}
                                  alt=""
                                  className="w-16 h-16 object-cover rounded"
                                  onError={(e) => {
                                    (e.target as HTMLImageElement).src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="64" height="64"%3E%3Crect fill="%23e5e7eb" width="64" height="64"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" dy=".3em" fill="%239ca3af" font-size="12"%3ENo img%3C/text%3E%3C/svg%3E';
                                  }}
                                />
                              ) : (
                                <div className="w-16 h-16 bg-gray-200 rounded flex items-center justify-center">
                                  <span className="text-gray-400 text-xs">No img</span>
                                </div>
                              )}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="font-medium text-gray-900 text-sm line-clamp-2">
                                {product.base_product.name}
                              </div>
                              <div className="text-xs text-gray-500 mt-1">
                                SKU: {product.base_product.sku}
                              </div>
                              <div className="text-sm font-bold text-cyan-600 mt-1">
                                {formatPrice(product.base_product.current_price)}
                              </div>
                            </div>
                          </div>
                        </td>

                        {/* Retailer Columns */}
                        {allRetailers.map((retailer) => {
                          const matches = retailerMatchesMap.get(retailer) || [];
                          
                          return (
                            <td key={retailer} className="px-4 py-4 align-top">
                              {matches.length === 0 ? (
                                <div className="text-center text-gray-400 text-sm py-4">-</div>
                              ) : (
                                <div className="space-y-3">
                                  {matches.map((match) => (
                                    <div
                                      key={match.match_id}
                                      className="border border-gray-200 rounded-lg p-3 bg-gray-50"
                                    >
                                      <div className="flex items-start gap-3">
                                        <div className="w-12 h-12 flex-shrink-0">
                                          {match.candidate_product.image ? (
                                            <img
                                              src={match.candidate_product.image}
                                              alt=""
                                              className="w-12 h-12 object-cover rounded"
                                              onError={(e) => {
                                                (e.target as HTMLImageElement).src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="48" height="48"%3E%3Crect fill="%23e5e7eb" width="48" height="48"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" dy=".3em" fill="%239ca3af" font-size="10"%3ENo img%3C/text%3E%3C/svg%3E';
                                              }}
                                            />
                                          ) : (
                                            <div className="w-12 h-12 bg-gray-200 rounded flex items-center justify-center">
                                              <span className="text-gray-400 text-xs">No</span>
                                            </div>
                                          )}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                          <div className="font-medium text-gray-900 text-xs line-clamp-2">
                                            {match.candidate_product.name}
                                          </div>
                                          <div className="text-xs text-gray-500 mt-1">
                                            {match.candidate_product.sku}
                                          </div>
                                          <div className="text-sm font-bold text-cyan-600 mt-1">
                                            {formatPrice(match.candidate_product.current_price)}
                                          </div>
                                          {match.confidence_score !== null && (
                                            <div className="text-xs text-gray-500 mt-1">
                                              Conf: {(match.confidence_score * 100).toFixed(0)}%
                                            </div>
                                          )}
                                        </div>
                                      </div>
                                      <div className="flex gap-2 mt-3">
                                        <button
                                          onClick={() => handleVerify(match.match_id, true)}
                                          className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 bg-green-500 text-white rounded text-xs hover:bg-green-600 transition-colors"
                                        >
                                          <Check className="w-3 h-3" />
                                          Same
                                        </button>
                                        <button
                                          onClick={() => handleVerify(match.match_id, false)}
                                          className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 bg-red-500 text-white rounded text-xs hover:bg-red-600 transition-colors"
                                        >
                                          <X className="w-3 h-3" />
                                          Diff
                                        </button>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Loading More Indicator */}
          {!isLoading && hasMore && (
            <div className="text-center py-8">
              {isLoadingMore ? (
                <div className="flex items-center justify-center gap-2">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-cyan-500"></div>
                  <span className="text-gray-500">Loading more products...</span>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="text-gray-500">
                    Showing {displayedProducts.length} of {filteredProducts.length} products
                  </div>
                  <button
                    onClick={loadMore}
                    className="px-6 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition-colors"
                  >
                    Load More
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
