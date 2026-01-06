'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import { MainLayout } from '@/components/layout/MainLayout';
import { ArrowLeft, ExternalLink, Check, X, Plus, ChevronDown, ChevronUp, RotateCcw, TrendingUp } from 'lucide-react';
import { apiFetch } from '@/lib/api';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

interface Product {
  product_id: number;
  sku: string;
  name: string;
  brand: string | null;
  category: string | null;
  current_price: number | null;
  original_price: number | null;
  link: string | null;
  image: string | null;
  retailer_name: string;
  retailer_id: string;
}

interface Match {
  match_id: number;
  is_same: boolean | null;
  confidence_score: number | null;
  reason: string | null;
  match_type: string;
  verified_by_user: boolean;
  product: Product;
}

interface ProductDetailData {
  product: Product;
  matches: Match[];
  total_matches: number;
}

interface PriceHistoryPoint {
  price: number;
  date: string;
}

interface PriceHistoryProduct {
  product_id: number;
  name: string;
  retailer: string;
  history: PriceHistoryPoint[];
}

interface PriceHistoryData {
  base_product: PriceHistoryProduct;
  matched_products: PriceHistoryProduct[];
}

// All competitor retailers configuration
const COMPETITORS = [
  { id: 'hp', name: 'HomePro', nameTh: 'โฮมโปร', color: '#1E88E5', bgClass: 'bg-blue-500', logo: '/logos/homepro.png' },
  { id: 'mgh', name: 'MegaHome', nameTh: 'เมกาโฮม', color: '#43A047', bgClass: 'bg-green-500', logo: '/logos/megahome.png' },
  { id: 'btv', name: 'Boonthavorn', nameTh: 'บุญถาวร', color: '#7B1FA2', bgClass: 'bg-purple-500', logo: '/logos/boonthavorn.png' },
  { id: 'gbh', name: 'Global House', nameTh: 'โกลบอลเฮ้าส์', color: '#F57C00', bgClass: 'bg-orange-500', logo: '/logos/globalhouse.png' },
  { id: 'dh', name: 'Do Home', nameTh: 'ดูโฮม', color: '#E64A19', bgClass: 'bg-red-500', logo: '/logos/dohome.png' },
];


export default function ProductDetailPage() {
  const params = useParams();
  const router = useRouter();
  const productId = params.id as string;

  const [data, setData] = useState<ProductDetailData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [collapsedRetailers, setCollapsedRetailers] = useState<Set<string>>(new Set());
  const [isRescraping, setIsRescraping] = useState(false);
  const [rescrapeResult, setRescrapeResult] = useState<{success: boolean; message: string} | null>(null);
  const [priceHistory, setPriceHistory] = useState<PriceHistoryData | null>(null);
  const [historyDays, setHistoryDays] = useState<number>(30);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  useEffect(() => {
    if (productId) {
      fetchProductDetail();
    }
  }, [productId]);

  useEffect(() => {
    if (productId) {
      fetchPriceHistory();
    }
  }, [productId, historyDays]);

  const fetchPriceHistory = async () => {
    setIsLoadingHistory(true);
    try {
      const response = await apiFetch(`/api/products/${productId}/price-history?days=${historyDays}`);
      if (response.ok) {
        const result = await response.json();
        setPriceHistory(result);
      }
    } catch (err) {
      console.error('Error fetching price history:', err);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const fetchProductDetail = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiFetch(`/api/products/${productId}`);
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Product not found');
        }
        throw new Error('Failed to fetch product details');
      }
      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
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
      setData((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          matches: prev.matches.map((m) =>
            m.match_id === matchId
              ? { ...m, verified_by_user: true, is_same: isSame }
              : m
          ),
        };
      });
    } catch (err) {
      console.error('Error verifying match:', err);
    }
  };

  const handleUndo = async (matchId: number) => {
    try {
      const response = await apiFetch(`/api/matches/${matchId}/undo`, {
        method: 'POST',
      });

      if (!response.ok) throw new Error('Failed to undo verification');

      // Update local state - reset to unverified
      setData((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          matches: prev.matches.map((m) =>
            m.match_id === matchId
              ? { ...m, verified_by_user: false, is_same: null }
              : m
          ),
        };
      });
    } catch (err) {
      console.error('Error undoing verification:', err);
    }
  };

  const handleRescrape = async () => {
    setIsRescraping(true);
    setRescrapeResult(null);
    try {
      const response = await apiFetch(`/api/products/${productId}/rescrape`, {
        method: 'POST',
      });

      if (!response.ok) throw new Error('Failed to rescrape products');

      const result = await response.json();

      // Show result message
      const successCount = result.successful || 0;
      const failedCount = result.failed || 0;
      setRescrapeResult({
        success: failedCount === 0,
        message: `Updated ${successCount} product${successCount !== 1 ? 's' : ''}${failedCount > 0 ? `, ${failedCount} failed` : ''}`
      });

      // Refresh product data to show new prices
      await fetchProductDetail();

      // Clear message after 5 seconds
      setTimeout(() => setRescrapeResult(null), 5000);
    } catch (err) {
      console.error('Error rescraping products:', err);
      setRescrapeResult({
        success: false,
        message: 'Failed to rescrape products'
      });
      setTimeout(() => setRescrapeResult(null), 5000);
    } finally {
      setIsRescraping(false);
    }
  };

  // Count verified matches for rescrape button
  const verifiedMatchCount = data?.matches.filter(m => m.verified_by_user && m.is_same).length || 0;

  const formatPrice = (price: number | null) => {
    if (price === null) return '-';
    return `฿${price.toLocaleString()}`;
  };

  const getConfidenceColor = (score: number | null) => {
    if (score === null) return 'bg-gray-500';
    if (score >= 0.9) return 'bg-green-500';
    if (score >= 0.7) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getMatchTypeBadge = (type: string) => {
    const styles: Record<string, string> = {
      exact: 'bg-cyan-100 text-cyan-700',
      fuzzy: 'bg-yellow-100 text-yellow-700',
      manual: 'bg-purple-100 text-purple-700',
    };
    return styles[type] || 'bg-gray-100 text-gray-700';
  };

  const toggleRetailerCollapse = (retailerId: string) => {
    setCollapsedRetailers(prev => {
      const newSet = new Set(prev);
      if (newSet.has(retailerId)) {
        newSet.delete(retailerId);
      } else {
        newSet.add(retailerId);
      }
      return newSet;
    });
  };

  if (isLoading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading product details...</p>
          </div>
        </div>
      </MainLayout>
    );
  }

  if (error || !data) {
    return (
      <MainLayout>
        <div className="flex flex-col items-center justify-center min-h-[400px]">
          <p className="text-red-500 mb-4">{error || 'Product not found'}</p>
          <button
            onClick={() => router.push('/products')}
            className="text-cyan-500 hover:text-cyan-600 flex items-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Products
          </button>
        </div>
      </MainLayout>
    );
  }

  const { product, matches } = data;

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Breadcrumb & Back Button */}
        <div className="flex items-center gap-3 text-sm text-gray-500">
          <button
            onClick={() => router.back()}
            className="flex items-center gap-1 text-gray-600 hover:text-cyan-500 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>
          <span className="text-gray-300">|</span>
          <span>Products</span>
          <span>/</span>
          <span className="text-gray-900 truncate max-w-md">{product.name}</span>
        </div>

        {/* Page Header */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Product Comparison Detail</h1>
            <p className="text-gray-600 mt-1">Compare prices and verify product matches across retailers</p>
          </div>
          <div className="flex items-center gap-3">
            {rescrapeResult && (
              <span className={`text-sm px-3 py-1 rounded-full ${rescrapeResult.success ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                {rescrapeResult.message}
              </span>
            )}
            <button
              onClick={handleRescrape}
              disabled={isRescraping}
              className="flex items-center gap-2 px-4 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              title={`Resync Thai Watsadu + ${verifiedMatchCount} verified match${verifiedMatchCount !== 1 ? 'es' : ''}`}
            >
              <RotateCcw className={`w-4 h-4 ${isRescraping ? 'animate-spin' : ''}`} />
              {isRescraping ? 'Resyncing...' : 'Resync Prices'}
            </button>
          </div>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Side - My Product */}
          <div className="space-y-4">
            {/* Header */}
            <div className="bg-cyan-600 text-white px-4 py-3 rounded-t-lg flex items-center gap-2">
              <span className="bg-white text-cyan-600 text-xs font-semibold px-2 py-1 rounded">My Product</span>
              <span className="font-medium">{product.retailer_name}</span>
            </div>

            {/* Product Card */}
            <div className="bg-white rounded-b-lg shadow p-6 -mt-4">
              <div className="w-full h-64 relative mb-4">
                {product.image ? (
                  <>
                    <img
                      src={product.image}
                      alt={product.name}
                      className="w-full h-64 object-contain bg-gray-50 rounded-lg"
                      referrerPolicy="no-referrer"
                      onError={(e) => {
                        const target = e.target as HTMLImageElement;
                        target.style.display = 'none';
                        const fallback = target.nextElementSibling as HTMLElement;
                        if (fallback) fallback.style.display = 'flex';
                      }}
                    />
                    <div className="w-full h-64 bg-gray-100 rounded-lg items-center justify-center absolute top-0 left-0 hidden">
                      <span className="text-gray-400">No image available</span>
                    </div>
                  </>
                ) : (
                  <div className="w-full h-64 bg-gray-100 rounded-lg flex items-center justify-center">
                    <span className="text-gray-400">No image available</span>
                  </div>
                )}
              </div>

              <h2 className="text-xl font-semibold text-gray-900 mb-2">{product.name}</h2>

              <div className="space-y-2 text-sm text-gray-600">
                <div className="flex justify-between">
                  <span>SKU:</span>
                  <span className="text-gray-900">{product.sku}</span>
                </div>
                {product.brand && (
                  <div className="flex justify-between">
                    <span>Brand:</span>
                    <span className="text-gray-900">{product.brand}</span>
                  </div>
                )}
                {product.category && (
                  <div className="flex justify-between">
                    <span>Category:</span>
                    <span className="text-gray-900">{product.category}</span>
                  </div>
                )}
              </div>

              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="text-2xl font-bold text-cyan-600">
                  {formatPrice(product.current_price)}
                </div>
                {product.original_price && product.original_price > (product.current_price || 0) && (
                  <div className="text-sm text-gray-400 line-through">
                    {formatPrice(product.original_price)}
                  </div>
                )}
              </div>

              {product.link && (
                <a
                  href={product.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-4 flex items-center gap-2 text-cyan-500 hover:text-cyan-600"
                >
                  <ExternalLink className="w-4 h-4" />
                  View on {product.retailer_name}
                </a>
              )}
            </div>
          </div>

          {/* Right Side - Matched Products Grouped by Retailer */}
          <div className="space-y-4">
            {/* <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">Matched Products</h3>
              <span className="text-sm text-gray-500">
                {matches.length} matches across {COMPETITORS.length} retailers
              </span>
            </div> */}

            {/* Retailer Sections */}
            <div className="space-y-4">
              {COMPETITORS.map((competitor) => {
                // Get matches for this retailer
                const retailerMatches = matches.filter(
                  (m) => m.product.retailer_id === competitor.id ||
                         m.product.retailer_name === competitor.name
                );
                const needsReviewCount = retailerMatches.filter((m) => !m.verified_by_user).length;
                const isCollapsed = collapsedRetailers.has(competitor.id);

                return (
                  <div key={competitor.id} className="bg-white rounded-lg shadow overflow-hidden">
                    {/* Retailer Header - Clickable */}
                    <div
                      className="text-white px-4 py-3 flex items-center justify-between cursor-pointer hover:brightness-110 transition-all"
                      style={{ backgroundColor: competitor.color }}
                      onClick={() => toggleRetailerCollapse(competitor.id)}
                    >
                      <div className="flex items-center gap-3">
                        <Image
                          src={competitor.logo}
                          alt={competitor.name}
                          width={28}
                          height={28}
                          className="object-contain bg-white rounded p-1"
                        />
                        <div>
                          <span className="font-bold">{competitor.name}</span>
                          <span className="text-white/70 text-sm ml-2">{competitor.nameTh}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="bg-white/20 text-white text-xs font-medium px-2 py-1 rounded">
                          {retailerMatches.length} match{retailerMatches.length !== 1 ? 'es' : ''}
                        </span>
                        {needsReviewCount > 0 && (
                          <span className="bg-yellow-400 text-yellow-900 text-xs font-medium px-2 py-1 rounded">
                            {needsReviewCount} to review
                          </span>
                        )}
                        {isCollapsed ? (
                          <ChevronDown className="w-5 h-5 text-white/80" />
                        ) : (
                          <ChevronUp className="w-5 h-5 text-white/80" />
                        )}
                      </div>
                    </div>

                    {/* Matches List - Collapsible */}
                    {!isCollapsed && (
                    <div className="divide-y divide-gray-100">
                      {(() => {
                        // Check if all matches are rejected (verified as incorrect)
                        const allRejected = retailerMatches.length > 0 &&
                          retailerMatches.every((m) => m.verified_by_user && m.is_same === false);

                        // Check if any match is already marked as correct BY USER for this retailer
                        const hasCorrectMatch = retailerMatches.some((m) => m.is_same === true && m.verified_by_user === true);

                        if (retailerMatches.length === 0) {
                          return (
                            <div className="p-6 text-center">
                              <p className="text-gray-400 mb-4">No matches found for {competitor.name}</p>
                              <Link
                                href={`/manual-add?sku=${encodeURIComponent(product.sku)}&url=${encodeURIComponent(product.link || '')}&retailer=${competitor.id}`}
                                className="inline-flex items-center gap-2 px-4 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition-colors font-medium text-sm"
                              >
                                <Plus className="w-4 h-4" />
                                Add {competitor.name} Match
                              </Link>
                            </div>
                          );
                        }

                        return (
                          <>
                            {retailerMatches.map((match) => (
                              <div key={match.match_id} className="p-4 hover:bg-gray-50 transition-colors">
                                <div className="flex gap-4">
                                  <div className="w-20 h-20 flex-shrink-0 relative">
                                    {match.product.image ? (
                                      <>
                                        <img
                                          src={match.product.image}
                                          alt={match.product.name}
                                          className="w-20 h-20 object-contain bg-gray-50 rounded"
                                          referrerPolicy="no-referrer"
                                          onError={(e) => {
                                            const target = e.target as HTMLImageElement;
                                            target.style.display = 'none';
                                            const fallback = target.nextElementSibling as HTMLElement;
                                            if (fallback) fallback.style.display = 'flex';
                                          }}
                                        />
                                        <div className="w-20 h-20 bg-gray-100 rounded items-center justify-center absolute top-0 left-0 hidden">
                                          <span className="text-gray-400 text-xs">No img</span>
                                        </div>
                                      </>
                                    ) : (
                                      <div className="w-20 h-20 bg-gray-100 rounded flex items-center justify-center">
                                        <span className="text-gray-400 text-xs">No img</span>
                                      </div>
                                    )}
                                  </div>

                                  <div className="flex-1 min-w-0">
                                    <h4 className="font-medium text-gray-900 line-clamp-2">{match.product.name}</h4>
                                    <div className="mt-1 text-sm text-gray-500">
                                      <span>SKU: {match.product.sku}</span>
                                      {match.product.brand && <span className="ml-4">Brand: {match.product.brand}</span>}
                                    </div>
                                    {match.product.category && (
                                      <div className="text-sm text-gray-500">Category: {match.product.category}</div>
                                    )}
                                    {match.product.link && (
                                      <a
                                        href={match.product.link}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="mt-2 inline-flex items-center gap-1 text-sm text-cyan-500 hover:text-cyan-600"
                                      >
                                        <ExternalLink className="w-3 h-3" />
                                        View on {competitor.name}
                                      </a>
                                    )}
                                  </div>

                                  <div className="text-right flex-shrink-0">
                                    <div className="text-xl font-bold text-gray-900">
                                      {formatPrice(match.product.current_price)}
                                    </div>
                                    <div className="flex items-center gap-2 mt-1 justify-end">
                                      {/* <span className={`text-xs font-medium px-2 py-1 rounded ${getMatchTypeBadge(match.match_type)}`}>
                                        {match.match_type.charAt(0).toUpperCase() + match.match_type.slice(1)}
                                      </span> */}
                                      {match.confidence_score !== null && (
                                        <span className={`${getConfidenceColor(match.confidence_score)} text-white text-xs font-medium px-2 py-1 rounded`}>
                                          {Math.round(match.confidence_score * 100)}%
                                        </span>
                                      )}
                                    </div>
                                    {match.verified_by_user && (
                                      <span className={`text-xs font-medium mt-1 inline-block ${match.is_same ? 'text-green-600' : 'text-red-600'}`}>
                                        <Check className="w-3 h-3 inline mr-1" />
                                        {match.is_same ? 'Verified' : 'Rejected'}
                                      </span>
                                    )}
                                  </div>
                                </div>

                                {/* Verification Actions */}
                                <div className="mt-4 pt-3 border-t border-gray-100 flex justify-end gap-3">
                                  {match.verified_by_user ? (
                                    <>
                                      <button
                                        onClick={() => handleUndo(match.match_id)}
                                        className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors border border-gray-200"
                                      >
                                        <RotateCcw className="w-4 h-4" />
                                        Undo
                                      </button>
                                      <div className={`flex items-center gap-2 px-4 py-2 rounded-lg ${match.is_same ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                                        {match.is_same ? (
                                          <>
                                            <Check className="w-4 h-4" />
                                            <span className="font-medium">Correct Match</span>
                                          </>
                                        ) : (
                                          <>
                                            <X className="w-4 h-4" />
                                            <span className="font-medium">Incorrect Match</span>
                                          </>
                                        )}
                                      </div>
                                    </>
                                  ) : (
                                    <>
                                      <button
                                        onClick={() => handleVerify(match.match_id, false)}
                                        className="flex items-center gap-2 px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors border border-red-200"
                                      >
                                        <X className="w-4 h-4" />
                                        Incorrect
                                      </button>
                                      <button
                                        onClick={() => handleVerify(match.match_id, true)}
                                        disabled={hasCorrectMatch}
                                        className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors border ${
                                          hasCorrectMatch
                                            ? 'text-gray-400 border-gray-200 bg-gray-50 cursor-not-allowed'
                                            : 'text-green-600 hover:bg-green-50 border-green-200'
                                        }`}
                                      >
                                        <Check className="w-4 h-4" />
                                        Correct
                                      </button>
                                    </>
                                  )}
                                </div>
                              </div>
                            ))}
                            {/* Show Manual Add button when all matches are rejected */}
                            {allRejected && (
                              <div className="p-4 border-t border-gray-200 bg-gray-50 text-center">
                                <p className="text-gray-500 text-sm mb-3">All candidates rejected</p>
                                <Link
                                  href={`/manual-add?sku=${encodeURIComponent(product.sku)}&url=${encodeURIComponent(product.link || '')}&retailer=${competitor.id}`}
                                  className="inline-flex items-center gap-2 px-4 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition-colors font-medium text-sm"
                                >
                                  <Plus className="w-4 h-4" />
                                  Add {competitor.name} Match Manually
                                </Link>
                              </div>
                            )}
                          </>
                        );
                      })()}
                    </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Price History Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-cyan-500" />
              Price History
            </h2>
            <div className="flex gap-2">
              {[7, 30, 90, 180, 365].map((days) => (
                <button
                  key={days}
                  onClick={() => setHistoryDays(days)}
                  className={`px-3 py-1 text-sm rounded-lg transition-colors ${
                    historyDays === days
                      ? 'bg-cyan-500 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {days === 7 ? '7D' : days === 30 ? '1M' : days === 90 ? '3M' : days === 180 ? '6M' : '1Y'}
                </button>
              ))}
            </div>
          </div>

          {isLoadingHistory ? (
            <div className="h-80 flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-500"></div>
            </div>
          ) : priceHistory && (priceHistory.base_product.history.length > 0 || priceHistory.matched_products.some(p => p.history.length > 0)) ? (
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={(() => {
                    // Combine all price history into chart data
                    const allDates = new Set<string>();
                    priceHistory.base_product.history.forEach(h => allDates.add(h.date.split('T')[0]));
                    priceHistory.matched_products.forEach(p => p.history.forEach(h => allDates.add(h.date.split('T')[0])));

                    const sortedDates = Array.from(allDates).sort();

                    return sortedDates.map(date => {
                      const point: Record<string, string | number | null> = { date };

                      // Find base product price for this date
                      const basePrice = priceHistory.base_product.history.find(h => h.date.split('T')[0] === date);
                      point[priceHistory.base_product.retailer] = basePrice?.price ?? null;

                      // Find matched products prices for this date
                      priceHistory.matched_products.forEach(mp => {
                        const mpPrice = mp.history.find(h => h.date.split('T')[0] === date);
                        point[mp.retailer] = mpPrice?.price ?? null;
                      });

                      return point;
                    });
                  })()}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 12 }}
                    tickFormatter={(value: string) => {
                      const date = new Date(value);
                      return `${date.getDate()}/${date.getMonth() + 1}`;
                    }}
                  />
                  <YAxis
                    tick={{ fontSize: 12 }}
                    tickFormatter={(value: number) => `฿${value.toLocaleString()}`}
                  />
                  <Tooltip
                    formatter={(value: number) => [`฿${value?.toLocaleString() ?? '-'}`, '']}
                    labelFormatter={(label: string) => {
                      const date = new Date(label);
                      return date.toLocaleDateString('th-TH', { day: 'numeric', month: 'short', year: 'numeric' });
                    }}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey={priceHistory.base_product.retailer}
                    stroke="#06b6d4"
                    strokeWidth={2}
                    dot={false}
                    connectNulls
                  />
                  {priceHistory.matched_products.map((mp, index) => {
                    const colors = ['#1E88E5', '#43A047', '#7B1FA2', '#F57C00', '#E64A19'];
                    return (
                      <Line
                        key={mp.product_id}
                        type="monotone"
                        dataKey={mp.retailer}
                        stroke={colors[index % colors.length]}
                        strokeWidth={2}
                        dot={false}
                        connectNulls
                      />
                    );
                  })}
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-80 flex items-center justify-center text-gray-500">
              No price history data available for the selected period
            </div>
          )}
        </div>
      </div>
    </MainLayout>
  );
}
