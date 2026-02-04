'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import { MainLayout } from '@/components/layout/MainLayout';
import { ArrowLeft, ExternalLink, Check, X, Plus, ChevronDown, ChevronUp, RotateCcw, Loader2, RefreshCw, TrendingUp, TrendingDown, Download, Calendar, CheckCircle, AlertCircle } from 'lucide-react';
import { apiFetch } from '@/lib/api';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import './datepicker.css';
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
import { trackProductView, trackMatchVerification } from '@/lib/analytics';

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
  last_updated_at: string | null;
  scrape_fail_count: number;
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

interface WatchlistGroup {
  group_id: number;
  name: string;
  added_at: string | null;
}

// Product image component with loading state and timeout retry
function ProductImage({ src, alt, className }: { src: string | null; alt: string; className?: string }) {
  const [status, setStatus] = useState<'loading' | 'loaded' | 'error'>('loading');
  const [retryCount, setRetryCount] = useState(0);
  const [imgSrc, setImgSrc] = useState(src);
  const timeoutRef = React.useRef<NodeJS.Timeout | null>(null);
  const statusRef = React.useRef(status);

  // Keep ref in sync with status
  statusRef.current = status;

  // Reset when src changes
  useEffect(() => {
    if (!src) {
      setStatus('error');
      return;
    }
    setStatus('loading');
    setImgSrc(src);
    setRetryCount(0);
  }, [src]);

  // Handle timeout for loading - only runs when status is 'loading'
  useEffect(() => {
    if (status !== 'loading' || !src) {
      return;
    }

    timeoutRef.current = setTimeout(() => {
      // Check current status via ref to avoid stale closure
      if (statusRef.current === 'loading') {
        if (retryCount < 3) {
          const newSrc = src + (src.includes('?') ? '&' : '?') + `_t=${Date.now()}`;
          setImgSrc(newSrc);
          setRetryCount(prev => prev + 1);
        } else {
          setStatus('error');
        }
      }
    }, 8000);

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [status, src, retryCount]);

  const handleManualRetry = () => {
    setRetryCount(0);
    setImgSrc(src);
    setStatus('loading');
  };

  if (!src || status === 'error') {
    return (
      <div className={`bg-gray-100 rounded-lg flex flex-col items-center justify-center gap-2 ${className}`}>
        <span className="text-gray-400">No image available</span>
        {src && (
          <button
            onClick={handleManualRetry}
            className="text-cyan-500 hover:text-cyan-600 text-sm flex items-center gap-1"
          >
            <RefreshCw className="w-3 h-3" />
            Retry
          </button>
        )}
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      {status === 'loading' && (
        <div className="absolute inset-0 bg-gray-50 rounded-lg flex items-center justify-center z-10">
          <Loader2 className="w-8 h-8 text-cyan-500 animate-spin" />
        </div>
      )}
      <img
        src={imgSrc || ''}
        alt={alt}
        className={`w-full h-full object-contain bg-gray-50 rounded-lg ${status === 'loading' ? 'opacity-0' : 'opacity-100'}`}
        referrerPolicy="no-referrer"
        loading="eager"
        onLoad={() => setStatus('loaded')}
        onError={() => {
          if (retryCount < 3) {
            const newSrc = src + (src.includes('?') ? '&' : '?') + `_t=${Date.now()}`;
            setImgSrc(newSrc);
            setRetryCount(prev => prev + 1);
          } else {
            setStatus('error');
          }
        }}
      />
    </div>
  );
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
  const [showCustomRange, setShowCustomRange] = useState(false);
  const [customStartDate, setCustomStartDate] = useState<Date | null>(null);
  const [customEndDate, setCustomEndDate] = useState<Date | null>(null);
  const [watchlistGroups, setWatchlistGroups] = useState<WatchlistGroup[]>([]);
  const [showAddWatchlistModal, setShowAddWatchlistModal] = useState(false);
  const [allWatchlistGroups, setAllWatchlistGroups] = useState<{group_id: number; name: string}[]>([]);
  const [selectedWatchlistId, setSelectedWatchlistId] = useState<string>('');
  const [isAddingToWatchlist, setIsAddingToWatchlist] = useState(false);

  useEffect(() => {
    if (productId) {
      fetchProductDetail();
      fetchWatchlistGroups();
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

  const fetchWatchlistGroups = async () => {
    try {
      const response = await apiFetch(`/api/products/${productId}/watchlist-groups`);
      if (response.ok) {
        const result = await response.json();
        setWatchlistGroups(result.groups || []);
      }
    } catch (err) {
      console.error('Error fetching watchlist groups:', err);
    }
  };

  const fetchAllWatchlistGroups = async () => {
    try {
      const response = await apiFetch('/api/watchlist/sku-groups');
      if (response.ok) {
        const result = await response.json();
        setAllWatchlistGroups(result.groups || []);
      }
    } catch (err) {
      console.error('Error fetching all watchlist groups:', err);
    }
  };

  const exportPriceHistory = async () => {
    if (!productId) return;

    try {
      const response = await apiFetch(`/api/products/${productId}/price-history/export?days=${historyDays}`);
      if (!response.ok) {
        throw new Error('Failed to export price history');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      const now = new Date();
      const timestamp = now.getFullYear().toString() +
        (now.getMonth() + 1).toString().padStart(2, '0') +
        now.getDate().toString().padStart(2, '0') + '_' +
        now.getHours().toString().padStart(2, '0') +
        now.getMinutes().toString().padStart(2, '0') +
        now.getSeconds().toString().padStart(2, '0');
      link.download = `price_history_export_${timestamp}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting price history:', error);
    }
  };

  const handleAddToWatchlist = async () => {
    if (!selectedWatchlistId || !data?.product) return;

    setIsAddingToWatchlist(true);
    try {
      const response = await apiFetch(`/api/watchlist/sku-groups/${selectedWatchlistId}/products`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sku: data.product.sku })
      });

      if (response.ok) {
        // Refresh the product's watchlist groups
        await fetchWatchlistGroups();
        setShowAddWatchlistModal(false);
        setSelectedWatchlistId('');
      } else {
        const error = await response.json();
        alert(error.detail || 'Failed to add to watchlist');
      }
    } catch (err) {
      console.error('Error adding to watchlist:', err);
      alert('Failed to add to watchlist');
    } finally {
      setIsAddingToWatchlist(false);
    }
  };

  const handleOpenAddWatchlistModal = () => {
    fetchAllWatchlistGroups();
    setShowAddWatchlistModal(true);
  };

  const handleRemoveFromWatchlist = async (groupId: number, groupName: string) => {
    if (!data?.product) return;

    const confirmed = window.confirm(`Remove ${data.product.sku} from "${groupName}"?`);
    if (!confirmed) return;

    try {
      const response = await apiFetch(`/api/watchlist/sku-groups/${groupId}/products/${data.product.sku}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        // Refresh the product's watchlist groups
        await fetchWatchlistGroups();
      } else {
        const error = await response.json();
        alert(error.detail || 'Failed to remove from watchlist');
      }
    } catch (err) {
      console.error('Error removing from watchlist:', err);
      alert('Failed to remove from watchlist');
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
      
      // Track product view
      if (result?.product) {
        trackProductView(
          result.product.product_id,
          result.product.name || 'Unknown Product',
          result.product.retailer_name || 'Unknown Retailer'
        );
      }
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
      
      // Track match verification
      trackMatchVerification(matchId, isSame);
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

  const formatLastUpdated = (dateStr: string | null) => {
    if (!dateStr) return 'Never';
    // Database stores UTC timestamps - ensure we parse as UTC
    // If the string doesn't have timezone info, append 'Z' to indicate UTC
    const utcDateStr = dateStr.endsWith('Z') || dateStr.includes('+') ? dateStr : dateStr + 'Z';
    const date = new Date(utcDateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    return date.toLocaleDateString('th-TH', { day: 'numeric', month: 'short', year: 'numeric' });
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
          <div className="flex flex-col self-stretch">
            <div className="bg-white rounded-lg shadow overflow-hidden flex-1 flex flex-col">
              {/* Header */}
              <div className="bg-cyan-600 text-white px-4 py-3 flex items-center gap-2 flex-shrink-0">
                <span className="bg-white text-cyan-600 text-xs font-semibold px-2 py-1 rounded">My Product</span>
                <span className="font-medium">{product.retailer_name}</span>
              </div>

              {/* Product Card Content */}
              <div className="p-6 flex-1 flex flex-col">
              <ProductImage
                src={product.image}
                alt={product.name}
                className="w-full h-64 mb-4"
              />

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
                <div className="pt-2 border-t border-gray-100">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-gray-500">Watchlist Groups:</span>
                    <button
                      onClick={handleOpenAddWatchlistModal}
                      className="flex items-center gap-1 px-2 py-1 text-xs text-cyan-600 hover:text-cyan-700 hover:bg-cyan-50 rounded transition-colors"
                      title="Add to watchlist"
                    >
                      <Plus className="w-3 h-3" />
                      Add
                    </button>
                  </div>
                  {watchlistGroups.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {watchlistGroups.map((group) => (
                        <div
                          key={group.group_id}
                          className="inline-flex items-center gap-1 px-2.5 py-1 bg-cyan-50 text-cyan-700 rounded-md text-xs font-medium group"
                        >
                          <Link
                            href={`/products?watchlist=${group.group_id}`}
                            className="hover:underline"
                            title={`View products in ${group.name}`}
                          >
                            {group.name}
                          </Link>
                          <button
                            onClick={() => handleRemoveFromWatchlist(group.group_id, group.name)}
                            className="ml-1 p-0.5 hover:bg-cyan-200 rounded transition-colors"
                            title={`Remove from ${group.name}`}
                          >
                            <X className="w-3 h-3" />
                          </button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <span className="text-gray-400 text-sm">None</span>
                  )}
                </div>
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

              {/* View link and Updated timestamp on same row */}
              <div className="mt-4 flex items-center justify-between">
                {product.link && (
                  <a
                    href={product.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-cyan-500 hover:text-cyan-600"
                  >
                    <ExternalLink className="w-4 h-4" />
                    View on {product.retailer_name}
                  </a>
                )}
                <div className="text-sm text-gray-500">
                  Updated: {formatLastUpdated(product.last_updated_at)}
                </div>
              </div>

              {/* Product Status Indicator */}
              <div className="mt-4">
                {product.scrape_fail_count >= 3 ? (
                  <div className="flex items-center gap-2 px-3 py-2 bg-red-50 border border-red-200 rounded-lg">
                    <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-red-800">Inactive Product</p>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 px-3 py-2 bg-green-50 border border-green-200 rounded-lg">
                    <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-green-800">Active Product</p>
                    </div>
                  </div>
                )}
              </div>

              {/* Spacer to push content to bottom */}
              <div className="flex-1"></div>
              </div>
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
                                  <ProductImage
                                    src={match.product.image}
                                    alt={match.product.name}
                                    className="w-20 h-20 flex-shrink-0"
                                  />

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
                                    <div className="text-xs text-gray-400 mt-1">
                                      Updated: {formatLastUpdated(match.product.last_updated_at)}
                                    </div>
                                  </div>
                                </div>

                                {/* Verification Actions */}
                                <div className="mt-4 pt-3 border-t border-gray-100 flex justify-between items-center gap-3">
                                  {/* Left: Active/Inactive Status */}
                                  <div>
                                    {match.verified_by_user && match.is_same && (
                                      match.product.scrape_fail_count >= 3 ? (
                                        <div className="flex items-center gap-1.5 text-xs text-red-600 font-medium">
                                          <AlertCircle className="w-4 h-4" />
                                          Inactive Product
                                        </div>
                                      ) : (
                                        <div className="flex items-center gap-1.5 text-xs text-green-600 font-medium">
                                          <CheckCircle className="w-4 h-4" />
                                          Active Product
                                        </div>
                                      )
                                    )}
                                  </div>

                                  {/* Right: Verification Buttons */}
                                  <div className="flex gap-3">
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
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-6">
            <h2 className="text-lg font-semibold text-gray-900">Price History</h2>
            <div className="flex flex-wrap items-center gap-2">
              {[
                { days: 1, label: '1 Day' },
                { days: 7, label: '1 Week' },
                { days: 30, label: '1 Month' },
                { days: 90, label: '3 Months' },
                { days: 180, label: '6 Months' },
                { days: 365, label: '1 Year' },
              ].map(({ days, label }) => (
                <button
                  key={days}
                  onClick={() => {
                    setHistoryDays(days);
                    setShowCustomRange(false);
                  }}
                  className={`px-3 h-8 text-sm rounded-md font-medium transition-colors ${
                    historyDays === days && !showCustomRange
                      ? 'bg-cyan-500 text-white hover:bg-cyan-600'
                      : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-300'
                  }`}
                >
                  {label}
                </button>
              ))}
              <button
                onClick={() => setShowCustomRange(!showCustomRange)}
                className={`px-3 h-8 text-sm rounded-md font-medium transition-colors ${
                  showCustomRange
                    ? 'bg-cyan-500 text-white hover:bg-cyan-600'
                    : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-300'
                }`}
              >
                Custom
              </button>
              <button
                onClick={exportPriceHistory}
                disabled={!priceHistory}
                className="px-3 h-8 text-sm rounded-md font-medium transition-colors bg-white text-gray-600 hover:bg-gray-100 border border-gray-300 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Download className="h-4 w-4" />
                Export
              </button>
            </div>
          </div>

          {/* Custom Date Range Picker */}
          {showCustomRange && (
            <div className="flex flex-wrap items-center gap-4 mb-6">
              <div className="flex items-center gap-2">
                <label className="text-sm text-gray-700">From:</label>
                <div className="relative">
                  <DatePicker
                    selected={customStartDate}
                    onChange={(date: Date | null) => {
                      setCustomStartDate(date);
                      // If start date is after end date, clear end date
                      if (date && customEndDate && date > customEndDate) {
                        setCustomEndDate(null);
                      }
                    }}
                    selectsStart
                    startDate={customStartDate}
                    endDate={customEndDate}
                    maxDate={new Date()}
                    placeholderText="Start date"
                    dateFormat="MMM d, yyyy"
                    className="pl-10 pr-3 py-2 text-sm border border-gray-300 bg-white rounded-md text-gray-700 focus:outline-none focus:ring-2 focus:ring-cyan-500 cursor-pointer transition-colors w-40"
                    wrapperClassName="w-full"
                  />
                  <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none z-10" />
                </div>
              </div>

              <div className="flex items-center gap-2">
                <label className="text-sm text-gray-700">To:</label>
                <div className="relative">
                  <DatePicker
                    selected={customEndDate}
                    onChange={(date: Date | null) => setCustomEndDate(date)}
                    selectsEnd
                    startDate={customStartDate}
                    endDate={customEndDate}
                    minDate={customStartDate || undefined}
                    maxDate={new Date()}
                    placeholderText="End date"
                    dateFormat="MMM d, yyyy"
                    className="pl-10 pr-3 py-2 text-sm border border-gray-300 bg-white rounded-md text-gray-700 focus:outline-none focus:ring-2 focus:ring-cyan-500 cursor-pointer transition-colors w-40"
                    wrapperClassName="w-full"
                  />
                  <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none z-10" />
                </div>
              </div>

              <button
                onClick={() => {
                  if (customStartDate && customEndDate) {
                    // Calculate days difference
                    const diffTime = Math.abs(customEndDate.getTime() - customStartDate.getTime());
                    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                    setHistoryDays(diffDays);
                  }
                }}
                disabled={!customStartDate || !customEndDate}
                className="ml-auto px-3 h-9 text-sm rounded-md font-medium bg-cyan-500 text-white hover:bg-cyan-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Apply
              </button>
            </div>
          )}

          {isLoadingHistory ? (
            <div className="h-[350px] flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-500"></div>
            </div>
          ) : priceHistory && (priceHistory.base_product.history.length > 0 || priceHistory.matched_products.some(p => p.history.length > 0)) ? (
            <div className="space-y-6">
              {/* Price Stats Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {(() => {
                  // Calculate lowest and highest prices
                  const allPrices: { price: number; retailer: string; date: string }[] = [];

                  priceHistory.base_product.history.forEach(h => {
                    allPrices.push({
                      price: h.price,
                      retailer: priceHistory.base_product.retailer,
                      date: h.date
                    });
                  });

                  priceHistory.matched_products.forEach(mp => {
                    mp.history.forEach(h => {
                      allPrices.push({
                        price: h.price,
                        retailer: mp.retailer,
                        date: h.date
                      });
                    });
                  });

                  const lowestPrice = allPrices.reduce((min, curr) =>
                    curr.price < min.price ? curr : min
                  , allPrices[0]);

                  const highestPrice = allPrices.reduce((max, curr) =>
                    curr.price > max.price ? curr : max
                  , allPrices[0]);

                  return (
                    <>
                      <div className="flex items-center gap-3 p-4 bg-green-50 rounded-lg border border-green-200">
                        <div className="p-2 bg-green-100 rounded-full">
                          <TrendingDown className="h-5 w-5 text-green-600" />
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Lowest Price</p>
                          <p className="text-xl font-bold text-green-600">
                            ฿{lowestPrice.price.toLocaleString()}
                          </p>
                          <p className="text-xs text-gray-500">
                            {lowestPrice.retailer} • {new Date(lowestPrice.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-3 p-4 bg-red-50 rounded-lg border border-red-200">
                        <div className="p-2 bg-red-100 rounded-full">
                          <TrendingUp className="h-5 w-5 text-red-600" />
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Highest Price</p>
                          <p className="text-xl font-bold text-red-600">
                            ฿{highestPrice.price.toLocaleString()}
                          </p>
                          <p className="text-xs text-gray-500">
                            {highestPrice.retailer} • {new Date(highestPrice.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                          </p>
                        </div>
                      </div>
                    </>
                  );
                })()}
              </div>

              {/* Chart */}
              <div className="h-[350px] w-full">
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
                    <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200" />
                    <XAxis
                      dataKey="date"
                      tick={{ fontSize: 12 }}
                      className="text-gray-600"
                      tickFormatter={(value: string) => {
                        const date = new Date(value);
                        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                      }}
                    />
                    <YAxis
                      tick={{ fontSize: 12 }}
                      className="text-gray-600"
                      tickFormatter={(value: number) => `฿${value.toLocaleString()}`}
                    />
                    <Tooltip
                      formatter={(value: number) => [`฿${value?.toLocaleString() ?? '-'}`, '']}
                      labelFormatter={(label: string) => {
                        const date = new Date(label);
                        return date.toLocaleDateString('th-TH', { day: 'numeric', month: 'short', year: 'numeric' });
                      }}
                    />
                    <Legend
                      wrapperStyle={{ paddingTop: '20px' }}
                      content={(props) => {
                        const { payload } = props;
                        return (
                          <ul className="flex justify-center gap-4 flex-wrap">
                            {payload?.map((entry: any, index: number) => (
                              <li key={`legend-${index}`} className="flex items-center gap-2">
                                <div
                                  className="w-3 h-3 rounded-full"
                                  style={{ backgroundColor: entry.color }}
                                />
                                <span className="text-sm text-gray-600">{entry.value}</span>
                              </li>
                            ))}
                          </ul>
                        );
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey={priceHistory.base_product.retailer}
                      stroke="#06b6d4"
                      strokeWidth={3}
                      dot={false}
                      connectNulls
                    />
                    {priceHistory.matched_products.map((mp, index) => {
                      // Map retailer names to their brand colors
                      const retailerColors: Record<string, string> = {
                        'HomePro': '#3b82f6',      // Blue
                        'Home Pro': '#3b82f6',      // Blue
                        'MegaHome': '#10b981',      // Green
                        'Mega Home': '#10b981',     // Green
                        'Boonthavorn': '#9333ea',   // Purple
                        'Global House': '#f97316',  // Orange
                        'GlobalHouse': '#f97316',   // Orange
                        'Do Home': '#ef4444',       // Red
                        'DoHome': '#ef4444',        // Red
                      };

                      // Get color by retailer name, fallback to default colors
                      const defaultColors = ['#3b82f6', '#10b981', '#9333ea', '#f97316', '#ef4444'];
                      const color = retailerColors[mp.retailer] || defaultColors[index % defaultColors.length];

                      return (
                        <Line
                          key={mp.product_id}
                          type="monotone"
                          dataKey={mp.retailer}
                          stroke={color}
                          strokeWidth={2}
                          dot={false}
                          connectNulls
                        />
                      );
                    })}
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Data point counter */}
              <div className="flex items-center">
                <h4 className="font-medium text-sm text-gray-500">
                  Showing {(() => {
                    const allDates = new Set<string>();
                    priceHistory.base_product.history.forEach(h => allDates.add(h.date.split('T')[0]));
                    priceHistory.matched_products.forEach(p => p.history.forEach(h => allDates.add(h.date.split('T')[0])));
                    return allDates.size;
                  })()} data points
                </h4>
              </div>
            </div>
          ) : (
            <div className="h-[350px] flex items-center justify-center text-gray-500">
              No price history data available for the selected period
            </div>
          )}
        </div>
      </div>

      {/* Add to Watchlist Modal */}
      {showAddWatchlistModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Add to Watchlist</h2>
            <p className="text-sm text-gray-600 mb-4">
              Select a watchlist group to add <span className="font-medium">{product.sku}</span>
            </p>

            <select
              value={selectedWatchlistId}
              onChange={(e) => setSelectedWatchlistId(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent mb-4"
            >
              <option value="">Select a watchlist group...</option>
              {allWatchlistGroups
                .filter(g => !watchlistGroups.some(wg => wg.group_id === g.group_id))
                .map((group) => (
                  <option key={group.group_id} value={group.group_id}>
                    {group.name}
                  </option>
                ))}
            </select>

            <div className="flex gap-3 justify-end">
              <button
                onClick={() => {
                  setShowAddWatchlistModal(false);
                  setSelectedWatchlistId('');
                }}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                disabled={isAddingToWatchlist}
              >
                Cancel
              </button>
              <button
                onClick={handleAddToWatchlist}
                disabled={!selectedWatchlistId || isAddingToWatchlist}
                className="px-4 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isAddingToWatchlist ? 'Adding...' : 'Add to Watchlist'}
              </button>
            </div>
          </div>
        </div>
      )}
    </MainLayout>
  );
}
