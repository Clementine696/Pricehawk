'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import { MainLayout } from '@/components/layout/MainLayout';
import { ArrowLeft, ExternalLink, Check, X, Plus } from 'lucide-react';
import { apiFetch } from '@/lib/api';

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

  useEffect(() => {
    if (productId) {
      fetchProductDetail();
    }
  }, [productId]);

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
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <Link href="/products" className="hover:text-cyan-500">
              Products
            </Link>
            <span>/</span>
            <span className="text-gray-900 truncate max-w-md">{product.name}</span>
          </div>
          <Link
            href="/products"
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to List
          </Link>
        </div>

        {/* Page Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Product Comparison Detail</h1>
          <p className="text-gray-600 mt-1">Compare prices and verify product matches across retailers</p>
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
              {product.image ? (
                <img
                  src={product.image}
                  alt={product.name}
                  className="w-full h-64 object-contain bg-gray-50 rounded-lg mb-4"
                />
              ) : (
                <div className="w-full h-64 bg-gray-100 rounded-lg flex items-center justify-center mb-4">
                  <span className="text-gray-400">No image available</span>
                </div>
              )}

              <h2 className="text-xl font-semibold text-gray-900 mb-2">{product.name}</h2>

              <div className="space-y-2 text-sm text-gray-600">
                <div className="flex justify-between">
                  <span>SKU:</span>
                  <span className="font-mono text-gray-900">{product.sku}</span>
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
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">Matched Products</h3>
              <span className="text-sm text-gray-500">
                {matches.length} matches across {COMPETITORS.length} retailers
              </span>
            </div>

            {/* Retailer Sections */}
            <div className="space-y-4">
              {COMPETITORS.map((competitor) => {
                // Get matches for this retailer
                const retailerMatches = matches.filter(
                  (m) => m.product.retailer_id === competitor.id ||
                         m.product.retailer_name === competitor.name
                );
                const needsReviewCount = retailerMatches.filter((m) => !m.verified_by_user).length;

                return (
                  <div key={competitor.id} className="bg-white rounded-lg shadow overflow-hidden">
                    {/* Retailer Header */}
                    <div
                      className="text-white px-4 py-3 flex items-center justify-between"
                      style={{ backgroundColor: competitor.color }}
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
                      </div>
                    </div>

                    {/* Matches List */}
                    <div className="divide-y divide-gray-100">
                      {retailerMatches.length === 0 ? (
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
                      ) : (
                        retailerMatches.map((match) => (
                          <div key={match.match_id} className="p-4 hover:bg-gray-50 transition-colors">
                            <div className="flex gap-4">
                              {match.product.image ? (
                                <img
                                  src={match.product.image}
                                  alt={match.product.name}
                                  className="w-20 h-20 object-contain bg-gray-50 rounded flex-shrink-0"
                                />
                              ) : (
                                <div className="w-20 h-20 bg-gray-100 rounded flex items-center justify-center flex-shrink-0">
                                  <span className="text-gray-400 text-xs">No img</span>
                                </div>
                              )}

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
                                  <span className={`text-xs font-medium px-2 py-1 rounded ${getMatchTypeBadge(match.match_type)}`}>
                                    {match.match_type.charAt(0).toUpperCase() + match.match_type.slice(1)}
                                  </span>
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
                                    className="flex items-center gap-2 px-4 py-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors border border-green-200"
                                  >
                                    <Check className="w-4 h-4" />
                                    Correct
                                  </button>
                                </>
                              )}
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}
