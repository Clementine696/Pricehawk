'use client';

import React, { useState, useEffect } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Search, ArrowRight, Check, X, AlertCircle } from 'lucide-react';
import { apiFetch } from '@/lib/api';

interface ProductMatch {
  match_id: number;
  base_product: {
    product_id: number;
    name: string;
    sku: string;
    retailer_name: string;
    current_price: number | null;
    image: string | null;
  };
  candidate_product: {
    product_id: number;
    name: string;
    sku: string;
    retailer_name: string;
    current_price: number | null;
    image: string | null;
  };
  is_same: boolean | null;
  confidence_score: number | null;
  reason: string | null;
  match_type: string;
  verified_by_user: boolean;
}

export default function ComparisonPage() {
  const [matches, setMatches] = useState<ProductMatch[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState<'all' | 'verified' | 'unverified'>('all');

  useEffect(() => {
    fetchMatches();
  }, []);

  const fetchMatches = async () => {
    setIsLoading(true);
    try {
      const response = await apiFetch('/api/matches');
      if (!response.ok) throw new Error('Failed to fetch matches');
      const data = await response.json();
      setMatches(data.matches || []);
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
      setMatches((prev) =>
        prev.map((m) =>
          m.match_id === matchId
            ? { ...m, verified_by_user: true, is_same: isSame }
            : m
        )
      );
    } catch (error) {
      console.error('Error verifying match:', error);
    }
  };

  const filteredMatches = matches.filter((match) => {
    const matchesSearch =
      match.base_product.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      match.candidate_product.name?.toLowerCase().includes(searchTerm.toLowerCase());

    if (filter === 'verified') return matchesSearch && match.verified_by_user;
    if (filter === 'unverified') return matchesSearch && !match.verified_by_user;
    return matchesSearch;
  });

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
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-2xl font-bold text-gray-900">{matches.length}</div>
            <div className="text-sm text-gray-500">Total Matches</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-2xl font-bold text-green-600">
              {matches.filter((m) => m.verified_by_user).length}
            </div>
            <div className="text-sm text-gray-500">Verified</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-2xl font-bold text-orange-600">
              {matches.filter((m) => !m.verified_by_user).length}
            </div>
            <div className="text-sm text-gray-500">Pending Review</div>
          </div>
        </div>

        {/* Search & Filters */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Search matches..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
            />
          </div>
          <div className="flex gap-2">
            {(['all', 'unverified', 'verified'] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  filter === f
                    ? 'bg-cyan-500 text-white'
                    : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                }`}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Matches List */}
        <div className="space-y-4">
          {isLoading ? (
            <div className="bg-white rounded-lg shadow p-12 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-500 mx-auto"></div>
              <p className="mt-2 text-gray-500">Loading matches...</p>
            </div>
          ) : filteredMatches.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-12 text-center">
              <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">No matches found</p>
            </div>
          ) : (
            filteredMatches.map((match) => (
              <div
                key={match.match_id}
                className={`bg-white rounded-lg shadow p-6 border-l-4 ${
                  match.verified_by_user
                    ? match.is_same
                      ? 'border-green-500'
                      : 'border-red-500'
                    : 'border-orange-500'
                }`}
              >
                <div className="flex flex-col lg:flex-row gap-6">
                  {/* Base Product */}
                  <div className="flex-1 bg-gray-50 rounded-lg p-4">
                    <div className="text-xs font-medium text-gray-500 uppercase mb-2">
                      Base Product
                    </div>
                    <div className="flex items-start gap-3">
                      <div className="w-16 h-16 relative flex-shrink-0">
                        {match.base_product.image ? (
                          <>
                            <img
                              src={match.base_product.image}
                              alt=""
                              className="w-16 h-16 object-cover rounded"
                              referrerPolicy="no-referrer"
                              onError={(e) => {
                                const target = e.target as HTMLImageElement;
                                target.style.display = 'none';
                                const fallback = target.nextElementSibling as HTMLElement;
                                if (fallback) fallback.style.display = 'flex';
                              }}
                            />
                            <div className="w-16 h-16 bg-gray-200 rounded items-center justify-center absolute top-0 left-0 hidden">
                              <span className="text-gray-400 text-xs">No img</span>
                            </div>
                          </>
                        ) : (
                          <div className="w-16 h-16 bg-gray-200 rounded flex items-center justify-center">
                            <span className="text-gray-400 text-xs">No img</span>
                          </div>
                        )}
                      </div>
                      <div className="flex-1">
                        <div className="font-medium text-gray-900 line-clamp-2">
                          {match.base_product.name}
                        </div>
                        <div className="text-sm text-gray-500 mt-1">
                          {match.base_product.retailer_name} | {match.base_product.sku}
                        </div>
                        <div className="text-lg font-bold text-cyan-600 mt-2">
                          {formatPrice(match.base_product.current_price)}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Arrow */}
                  <div className="flex items-center justify-center">
                    <ArrowRight className="w-6 h-6 text-gray-400" />
                  </div>

                  {/* Candidate Product */}
                  <div className="flex-1 bg-gray-50 rounded-lg p-4">
                    <div className="text-xs font-medium text-gray-500 uppercase mb-2">
                      Matched Product
                    </div>
                    <div className="flex items-start gap-3">
                      <div className="w-16 h-16 relative flex-shrink-0">
                        {match.candidate_product.image ? (
                          <>
                            <img
                              src={match.candidate_product.image}
                              alt=""
                              className="w-16 h-16 object-cover rounded"
                              referrerPolicy="no-referrer"
                              onError={(e) => {
                                const target = e.target as HTMLImageElement;
                                target.style.display = 'none';
                                const fallback = target.nextElementSibling as HTMLElement;
                                if (fallback) fallback.style.display = 'flex';
                              }}
                            />
                            <div className="w-16 h-16 bg-gray-200 rounded items-center justify-center absolute top-0 left-0 hidden">
                              <span className="text-gray-400 text-xs">No img</span>
                            </div>
                          </>
                        ) : (
                          <div className="w-16 h-16 bg-gray-200 rounded flex items-center justify-center">
                            <span className="text-gray-400 text-xs">No img</span>
                          </div>
                        )}
                      </div>
                      <div className="flex-1">
                        <div className="font-medium text-gray-900 line-clamp-2">
                          {match.candidate_product.name}
                        </div>
                        <div className="text-sm text-gray-500 mt-1">
                          {match.candidate_product.retailer_name} | {match.candidate_product.sku}
                        </div>
                        <div className="text-lg font-bold text-cyan-600 mt-2">
                          {formatPrice(match.candidate_product.current_price)}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex flex-col justify-center gap-3 min-w-[200px]">
                    {match.confidence_score !== null && (
                      <div className="text-center mb-2">
                        <div className="text-xs text-gray-500 uppercase">Confidence</div>
                        <div className={`text-lg font-bold ${getConfidenceColor(match.confidence_score)}`}>
                          {(match.confidence_score * 100).toFixed(0)}%
                        </div>
                      </div>
                    )}

                    {match.verified_by_user ? (
                      <div
                        className={`flex items-center justify-center gap-2 px-4 py-2 rounded-lg ${
                          match.is_same
                            ? 'bg-green-100 text-green-700'
                            : 'bg-red-100 text-red-700'
                        }`}
                      >
                        {match.is_same ? (
                          <>
                            <Check className="w-5 h-5" />
                            <span className="font-medium">Same Product</span>
                          </>
                        ) : (
                          <>
                            <X className="w-5 h-5" />
                            <span className="font-medium">Different</span>
                          </>
                        )}
                      </div>
                    ) : (
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleVerify(match.match_id, true)}
                          className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
                        >
                          <Check className="w-5 h-5" />
                          Same
                        </button>
                        <button
                          onClick={() => handleVerify(match.match_id, false)}
                          className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
                        >
                          <X className="w-5 h-5" />
                          Different
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                {/* Match Info */}
                {match.reason && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <div className="text-sm text-gray-600">
                      <span className="font-medium">Match Reason:</span> {match.reason}
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </MainLayout>
  );
}
