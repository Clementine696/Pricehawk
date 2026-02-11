'use client';

import { useState, useEffect } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { apiFetch } from '@/lib/api';
import { MapPin, Package, Settings, Download, TrendingDown, Loader2, RefreshCw } from 'lucide-react';
import Link from 'next/link';

interface LocationPrice {
  twd_sku: string;
  twd_name: string;
  gbh_sku: string;
  gbh_name: string;
  gbh_url: string;
  location_id: number;
  location_name_th: string;
  location_name_en: string;
  price: number;
  scraped_at: string;
  group_id: number;
  sdept: string;
}

interface GroupedData {
  [twdSku: string]: {
    twd_name: string;
    gbh_sku: string;
    gbh_name: string;
    gbh_url: string;
    sdept: string;
    prices: LocationPrice[];
    min_price: number;
    max_price: number;
  };
}

export default function PriceByLocationPage() {
  // State
  const [data, setData] = useState<LocationPrice[]>([]);
  const [groupedData, setGroupedData] = useState<GroupedData>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedGroup, setSelectedGroup] = useState<string>('all');
  const [selectedLocation, setSelectedLocation] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'sku' | 'price_range'>('sku');

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    // Group data by TWD SKU
    const grouped: GroupedData = {};

    data.forEach((item) => {
      if (!grouped[item.twd_sku]) {
        grouped[item.twd_sku] = {
          twd_name: item.twd_name,
          gbh_sku: item.gbh_sku,
          gbh_name: item.gbh_name,
          gbh_url: item.gbh_url,
          sdept: item.sdept,
          prices: [],
          min_price: Infinity,
          max_price: -Infinity,
        };
      }

      grouped[item.twd_sku].prices.push(item);

      if (item.price < grouped[item.twd_sku].min_price) {
        grouped[item.twd_sku].min_price = item.price;
      }
      if (item.price > grouped[item.twd_sku].max_price) {
        grouped[item.twd_sku].max_price = item.price;
      }
    });

    setGroupedData(grouped);
  }, [data]);

  const fetchData = async () => {
    setIsLoading(true);
    setError('');

    try {
      const response = await apiFetch('/api/location-prices');
      if (!response.ok) throw new Error('Failed to fetch location prices');
      const result = await response.json();
      setData(result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      const response = await apiFetch('/api/location-prices/export');
      if (!response.ok) throw new Error('Failed to export data');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `location-prices-${new Date().toISOString().split('T')[0]}.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      setError(err.message);
    }
  };

  // Get unique groups and locations for filters
  const uniqueGroups = [...new Set(data.map(d => d.sdept))].sort();
  const uniqueLocations = [...new Set(data.map(d => d.location_name_en))].sort();

  // Filter data
  const filteredData = Object.entries(groupedData).filter(([sku, product]) => {
    if (selectedGroup !== 'all' && product.sdept !== selectedGroup) return false;
    if (selectedLocation !== 'all' && !product.prices.some(p => p.location_name_en === selectedLocation)) return false;
    return true;
  });

  // Sort data
  const sortedData = [...filteredData].sort((a, b) => {
    if (sortBy === 'sku') {
      return a[0].localeCompare(b[0]);
    } else {
      const rangeA = a[1].max_price - a[1].min_price;
      const rangeB = b[1].max_price - b[1].min_price;
      return rangeB - rangeA;
    }
  });

  if (isLoading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-screen">
          <Loader2 className="h-8 w-8 animate-spin text-cyan-500" />
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="p-6 max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Price by Location
            </h1>
            <p className="text-gray-600">
              Compare prices across different GlobalHouse locations
            </p>
          </div>

          <div className="flex gap-3">
            <button
              onClick={fetchData}
              className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors flex items-center gap-2"
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
            </button>
            <button
              onClick={handleExport}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2"
            >
              <Download className="h-4 w-4" />
              Export
            </button>
            <Link
              href="/price-by-location/settings"
              className="px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 transition-colors flex items-center gap-2"
            >
              <Settings className="h-4 w-4" />
              Settings
            </Link>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {/* Empty State */}
        {data.length === 0 && !isLoading && (
          <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
            <MapPin className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              No location data yet
            </h3>
            <p className="text-gray-600 mb-6">
              Configure groups and locations in settings, then run the price updater service
            </p>
            <Link
              href="/price-by-location/settings"
              className="inline-flex items-center gap-2 px-6 py-3 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 transition-colors"
            >
              <Settings className="h-5 w-5" />
              Go to Settings
            </Link>
          </div>
        )}

        {/* Filters & Stats */}
        {data.length > 0 && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              {/* Stats */}
              <div className="bg-cyan-50 border border-cyan-200 rounded-lg p-4">
                <Package className="h-6 w-6 text-cyan-600 mb-2" />
                <p className="text-sm text-gray-600">Total Products</p>
                <p className="text-2xl font-bold text-cyan-600">
                  {Object.keys(groupedData).length}
                </p>
              </div>

              {/* Filters */}
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Filter by Group
                </label>
                <select
                  value={selectedGroup}
                  onChange={(e) => setSelectedGroup(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500"
                >
                  <option value="all">All Groups</option>
                  {uniqueGroups.map((group) => (
                    <option key={group} value={group}>
                      {group}
                    </option>
                  ))}
                </select>
              </div>

              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Filter by Location
                </label>
                <select
                  value={selectedLocation}
                  onChange={(e) => setSelectedLocation(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500"
                >
                  <option value="all">All Locations</option>
                  {uniqueLocations.map((location) => (
                    <option key={location} value={location}>
                      {location}
                    </option>
                  ))}
                </select>
              </div>

              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Sort by
                </label>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as any)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500"
                >
                  <option value="sku">SKU</option>
                  <option value="price_range">Price Range</option>
                </select>
              </div>
            </div>

            {/* Products List */}
            <div className="space-y-4">
              {sortedData.map(([twdSku, product]) => {
                const priceRange = product.max_price - product.min_price;
                const percentDiff = ((priceRange / product.min_price) * 100).toFixed(1);

                // Filter prices if location is selected
                const displayPrices = selectedLocation === 'all'
                  ? product.prices
                  : product.prices.filter(p => p.location_name_en === selectedLocation);

                return (
                  <div key={twdSku} className="bg-white border border-gray-200 rounded-lg p-6">
                    {/* Product Info */}
                    <div className="mb-4">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <h3 className="text-lg font-semibold text-gray-900 mb-1">
                            {product.gbh_name}
                          </h3>
                          <div className="flex items-center gap-4 text-sm text-gray-600">
                            <span>TWD SKU: {twdSku}</span>
                            <span>GBH SKU: {product.gbh_sku}</span>
                            <span className="px-2 py-1 bg-cyan-100 text-cyan-700 rounded">
                              {product.sdept}
                            </span>
                          </div>
                        </div>

                        {priceRange > 0 && (
                          <div className="text-right">
                            <div className="flex items-center gap-2 text-orange-600">
                              <TrendingDown className="h-5 w-5" />
                              <span className="text-lg font-bold">
                                ฿{priceRange.toFixed(2)}
                              </span>
                            </div>
                            <div className="text-sm text-gray-600">
                              {percentDiff}% difference
                            </div>
                          </div>
                        )}
                      </div>

                      <a
                        href={product.gbh_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-cyan-600 hover:underline"
                      >
                        View on GlobalHouse →
                      </a>
                    </div>

                    {/* Location Prices */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                      {displayPrices
                        .sort((a, b) => a.price - b.price)
                        .map((priceData) => {
                          const isCheapest = priceData.price === product.min_price;
                          const isExpensive = priceData.price === product.max_price && priceRange > 0;

                          return (
                            <div
                              key={`${priceData.location_id}`}
                              className={`p-4 rounded-lg border-2 ${
                                isCheapest
                                  ? 'bg-green-50 border-green-300'
                                  : isExpensive
                                  ? 'bg-red-50 border-red-300'
                                  : 'bg-gray-50 border-gray-200'
                              }`}
                            >
                              <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center gap-2">
                                  <MapPin className={`h-4 w-4 ${isCheapest ? 'text-green-600' : 'text-gray-500'}`} />
                                  <span className="font-medium text-gray-900">
                                    {priceData.location_name_en}
                                  </span>
                                </div>
                                {isCheapest && (
                                  <span className="px-2 py-1 bg-green-600 text-white text-xs rounded">
                                    Cheapest
                                  </span>
                                )}
                              </div>

                              <div className="text-sm text-gray-600 mb-2">
                                {priceData.location_name_th}
                              </div>

                              <div className="flex items-baseline gap-2">
                                <span className={`text-2xl font-bold ${isCheapest ? 'text-green-600' : 'text-gray-900'}`}>
                                  ฿{priceData.price.toFixed(2)}
                                </span>
                                {!isCheapest && priceRange > 0 && (
                                  <span className="text-sm text-red-600">
                                    +฿{(priceData.price - product.min_price).toFixed(2)}
                                  </span>
                                )}
                              </div>

                              <div className="text-xs text-gray-500 mt-2">
                                Updated: {new Date(priceData.scraped_at).toLocaleString()}
                              </div>
                            </div>
                          );
                        })}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* No results after filtering */}
            {sortedData.length === 0 && (
              <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
                <p className="text-gray-600">
                  No products match your filters
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </MainLayout>
  );
}
