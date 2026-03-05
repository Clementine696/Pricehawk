'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { MainLayout } from '@/components/layout/MainLayout';
import { ArrowLeft, MapPin, RotateCcw, Loader2, ExternalLink, ChevronDown, X } from 'lucide-react';
import { apiFetch } from '@/lib/api';

interface ProductDetail {
  twd_sku: string;
  twd_name: string;
  twd_price: number | null;
  twd_updated_at: string | null;
  brand: string | null;
  category: string | null;
  twd_url: string | null;
  gbh_sku: string;
  gbh_name: string;
  gbh_url: string | null;
  min_price: number | null;
  max_price: number | null;
  min_branch_name: string | null;
  max_branch_name: string | null;
  avg_price: number | null;
  branch_count: number;
  total_branches: number;
}

interface Branch {
  no: number;
  location_id: number;
  branch_name_th: string;
  branch_name_en: string;
  branch_code: string | null;
  postal_code: string | null;
  price: number | null;
  scraped_at: string | null;
  status: 'cheaper' | 'higher' | 'same' | 'unknown';
}

export default function PriceByLocationDetailPage() {
  const params = useParams();
  const sku = params.sku as string;

  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [locationFilter, setLocationFilter] = useState<'all' | 'cheaper' | 'higher' | 'same'>('all');
  const [selectedLocations, setSelectedLocations] = useState<number[]>([]);
  const [showLocationDropdown, setShowLocationDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchData();
  }, [sku]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowLocationDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchData = async () => {
    setIsLoading(true);
    setError('');
    try {
      const response = await apiFetch(`/api/location-prices/product/${sku}`);
      if (!response.ok) throw new Error('Failed to fetch product location prices');
      const result = await response.json();
      setProduct(result.product);
      setBranches(result.branches);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const formatPrice = (price: number | null) => {
    if (price === null || price === undefined) return '-';
    return `฿${price.toLocaleString('th-TH', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
  };

  const formatTimestamp = (timestamp: string | null) => {
    if (!timestamp) return '—';
    try {
      const date = new Date(timestamp);
      return date.toLocaleString('th-TH', {
        timeZone: 'Asia/Bangkok',
        day: '2-digit',
        month: '2-digit',
        year: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
      });
    } catch {
      return '—';
    }
  };

  const getStatusBadge = (status: Branch['status'], price: number | null, twd_price: number | null) => {
    if (status === 'cheaper') {
      const diff = twd_price && price ? twd_price - price : 0;
      return (
        <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
          Cheaper {diff > 0 ? `(-฿${diff.toLocaleString()})` : ''}
        </span>
      );
    }
    if (status === 'higher') {
      const diff = twd_price && price ? price - twd_price : 0;
      return (
        <span className="px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-600">
          Higher {diff > 0 ? `(+฿${diff.toLocaleString()})` : ''}
        </span>
      );
    }
    if (status === 'same') {
      return <span className="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">Same</span>;
    }
    return <span className="text-gray-400">-</span>;
  };

  const filteredBranches = branches.filter(b => {
    // Search filter
    const matchesSearch = !search ||
      b.branch_name_th.toLowerCase().includes(search.toLowerCase()) ||
      b.branch_name_en.toLowerCase().includes(search.toLowerCase());
    
    // Status filter
    const matchesStatusFilter = 
      locationFilter === 'all' ||
      (locationFilter === 'cheaper' && b.status === 'cheaper') ||
      (locationFilter === 'higher' && b.status === 'higher') ||
      (locationFilter === 'same' && b.status === 'same');
    
    // Location filter (selected branches)
    const matchesLocationFilter = 
      selectedLocations.length === 0 ||
      selectedLocations.includes(b.location_id);
    
    return matchesSearch && matchesStatusFilter && matchesLocationFilter;
  });

  const toggleLocation = (locationId: number) => {
    setSelectedLocations(prev =>
      prev.includes(locationId)
        ? prev.filter(id => id !== locationId)
        : [...prev, locationId]
    );
  };

  const clearLocationFilter = () => {
    setSelectedLocations([]);
  };

  if (isLoading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <Loader2 className="w-10 h-10 animate-spin text-cyan-500" />
        </div>
      </MainLayout>
    );
  }

  if (error || !product) {
    return (
      <MainLayout>
        <div className="p-6">
          <Link href="/price-by-location" className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6">
            <ArrowLeft className="w-4 h-4" />
            Back to Price by Location
          </Link>
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error || 'Product not found'}
          </div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Back link */}
        <Link href="/price-by-location" className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900">
          <ArrowLeft className="w-4 h-4" />
          Back to Price by Location
        </Link>

        {/* Product Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-1">{product.twd_name}</h1>
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <span className="text-gray-500">{product.twd_sku}</span>
            {product.brand && (
              <span className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full">{product.brand}</span>
            )}
            {product.category && (
              <span className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full">{product.category}</span>
            )}
            {product.twd_url && (
              <a href={product.twd_url} target="_blank" rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-cyan-600 hover:underline">
                Thai Watsadu <ExternalLink className="w-3 h-3" />
              </a>
            )}
            {product.gbh_url && (
              <a href={product.gbh_url} target="_blank" rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-cyan-600 hover:underline">
                Global House <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>
        </div>

        {/* Stats cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="bg-cyan-500 p-3 rounded-lg">
                <MapPin className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-500">My Price</p>
                <p className="text-2xl font-bold text-gray-900">{formatPrice(product.twd_price)}</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="bg-green-500 p-3 rounded-lg">
                <MapPin className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-500">Min Branch Price</p>
                <p className="text-2xl font-bold text-gray-900">{formatPrice(product.min_price)}</p>
                {product.min_branch_name && (
                  <p className="text-xs text-gray-500 mt-0.5">{product.min_branch_name}</p>
                )}
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="bg-red-500 p-3 rounded-lg">
                <MapPin className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-500">Max Branch Price</p>
                <p className="text-2xl font-bold text-gray-900">{formatPrice(product.max_price)}</p>
                {product.max_branch_name && (
                  <p className="text-xs text-gray-500 mt-0.5">{product.max_branch_name}</p>
                )}
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="bg-gray-500 p-3 rounded-lg">
                <MapPin className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-500">Branches with Data</p>
                <p className="text-2xl font-bold text-gray-900">{product.branch_count}/{product.total_branches}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Branch table */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-5 border-b border-gray-200 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Branch Price Comparison</h2>
              <p className="text-sm text-gray-500 mt-0.5">{product.total_branches} branches</p>
            </div>
            <div className="flex items-center gap-3">
              {/* Location Filter Buttons */}
              <div className="flex gap-1.5">
                <button
                  onClick={() => setLocationFilter('all')}
                  className={`px-4 py-1.5 text-xs rounded-lg transition-colors whitespace-nowrap w-[90px] ${
                    locationFilter === 'all'
                      ? 'bg-blue-100 text-blue-700 font-medium'
                      : 'text-gray-600 hover:bg-gray-100 border border-gray-300'
                  }`}
                >
                  All ({branches.length})
                </button>
                <button
                  onClick={() => setLocationFilter('cheaper')}
                  className={`px-4 py-1.5 text-xs rounded-lg transition-colors whitespace-nowrap w-[90px] ${
                    locationFilter === 'cheaper'
                      ? 'bg-green-100 text-green-700 font-medium'
                      : 'text-gray-600 hover:bg-gray-100 border border-gray-300'
                  }`}
                >
                  Cheaper ({branches.filter(b => b.status === 'cheaper').length})
                </button>
                <button
                  onClick={() => setLocationFilter('higher')}
                  className={`px-4 py-1.5 text-xs rounded-lg transition-colors whitespace-nowrap w-[90px] ${
                    locationFilter === 'higher'
                      ? 'bg-red-100 text-red-700 font-medium'
                      : 'text-gray-600 hover:bg-gray-100 border border-gray-300'
                  }`}
                >
                  Higher ({branches.filter(b => b.status === 'higher').length})
                </button>
                <button
                  onClick={() => setLocationFilter('same')}
                  className={`px-4 py-1.5 text-xs rounded-lg transition-colors whitespace-nowrap w-[90px] ${
                    locationFilter === 'same'
                      ? 'bg-gray-200 text-gray-700 font-medium'
                      : 'text-gray-600 hover:bg-gray-100 border border-gray-300'
                  }`}
                >
                  Same ({branches.filter(b => b.status === 'same').length})
                </button>
              </div>
              {/* Location Selector */}
              <div className="relative" ref={dropdownRef}>
                <button
                  onClick={() => setShowLocationDropdown(!showLocationDropdown)}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 border rounded-lg text-sm transition-colors ${
                    selectedLocations.length > 0
                      ? 'bg-blue-50 border-blue-300 text-blue-700'
                      : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <MapPin className="w-3.5 h-3.5" />
                  Locations
                  {selectedLocations.length > 0 && (
                    <span className="px-1.5 py-0.5 bg-blue-600 text-white text-xs rounded-full">
                      {selectedLocations.length}
                    </span>
                  )}
                  <ChevronDown className="w-3.5 h-3.5" />
                </button>
                
                {showLocationDropdown && (
                  <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 z-20 max-h-96 overflow-hidden flex flex-col">
                    <div className="p-3 border-b border-gray-200 flex items-center justify-between">
                      <span className="text-sm font-semibold text-gray-900">Filter by Branch</span>
                      {selectedLocations.length > 0 && (
                        <button
                          onClick={clearLocationFilter}
                          className="text-xs text-blue-600 hover:text-blue-700 font-medium"
                        >
                          Clear ({selectedLocations.length})
                        </button>
                      )}
                    </div>
                    <div className="overflow-y-auto flex-1">
                      {branches.map((branch) => (
                        <label
                          key={branch.location_id}
                          className="flex items-center gap-2 px-3 py-2 hover:bg-gray-50 cursor-pointer border-b border-gray-100 last:border-0"
                        >
                          <input
                            type="checkbox"
                            checked={selectedLocations.includes(branch.location_id)}
                            onChange={() => toggleLocation(branch.location_id)}
                            className="h-4 w-4 accent-blue-600 rounded flex-shrink-0"
                          />
                          <div className="flex-1 min-w-0">
                            <div className="text-sm text-gray-900 truncate">{branch.branch_name_th}</div>
                            <div className="text-xs text-gray-500 truncate">{branch.branch_name_en}</div>
                          </div>
                          {branch.price && (
                            <div className={`text-xs font-medium flex-shrink-0 ${
                              branch.status === 'cheaper' ? 'text-green-600' :
                              branch.status === 'higher' ? 'text-red-600' :
                              'text-gray-600'
                            }`}>
                              ฿{branch.price.toLocaleString()}
                            </div>
                          )}
                        </label>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              {/* Search */}
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search branch..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-3 pr-4 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-cyan-500 focus:border-transparent w-48"
                />
              </div>
              <button
                onClick={fetchData}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 border border-gray-300 rounded-lg text-sm hover:bg-gray-50 transition-colors"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                Refresh
              </button>
            </div>
          </div>

          <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
            <table className="w-full">
              <thead className="bg-gray-50 sticky top-0 z-10">
                <tr>
                  <th className="w-[60px] px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-50">No.</th>
                  <th className="w-[130px] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-50">Retailer</th>
                  <th className="w-[200px] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-50">Branch (TH)</th>
                  <th className="w-[180px] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-50">Branch (EN)</th>
                  <th className="w-[100px] px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-50">Postal Code</th>
                  <th className="w-[120px] px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-50">Price</th>
                  <th className="w-[140px] px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-50">Status</th>
                  <th className="w-[140px] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-50">Updated</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {/* TWD base price row */}
                <tr className="bg-cyan-50">
                  <td className="px-4 py-3 text-sm text-gray-400 text-center"></td>
                  <td className="px-4 py-3 text-sm font-medium text-cyan-700">Thai Watsadu</td>
                  <td className="px-4 py-3 text-sm font-medium text-cyan-700">
                    <div className="flex items-center gap-2">
                      <MapPin className="w-4 h-4 shrink-0" />
                      <span>เทพารักษ์</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">THEPHARAK</td>
                  <td className="px-4 py-3 text-sm text-gray-400 text-center"></td>
                  <td className="px-4 py-3 text-sm font-semibold text-cyan-700 text-right">{formatPrice(product.twd_price)}</td>
                  <td className="px-4 py-3 text-center">
                    <span className="px-2 py-1 rounded-full text-xs font-medium bg-cyan-100 text-cyan-700">My Price</span>
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-400">
                    {formatTimestamp(product.twd_updated_at)}
                  </td>
                </tr>

                {filteredBranches.map((branch) => (
                  <tr key={branch.location_id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 text-sm text-gray-500 text-center">{branch.no}</td>
                    <td className="px-4 py-3 text-sm text-gray-900">Global House</td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      <div className="flex items-center gap-2">
                        <MapPin className="w-4 h-4 text-gray-400 shrink-0" />
                        <span>{branch.branch_name_th}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">{branch.branch_name_en}</td>
                    <td className="px-4 py-3 text-sm text-gray-500 text-center">{branch.postal_code || '—'}</td>
                    <td className={`px-4 py-3 text-sm font-semibold text-right ${
                      branch.status === 'cheaper' ? 'text-green-600' :
                      branch.status === 'higher' ? 'text-red-600' :
                      'text-gray-900'
                    }`}>
                      {formatPrice(branch.price)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {getStatusBadge(branch.status, branch.price, product.twd_price)}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-400">
                      {formatTimestamp(branch.scraped_at)}
                    </td>
                  </tr>
                ))}

                {filteredBranches.length === 0 && (
                  <tr>
                    <td colSpan={8} className="px-4 py-8 text-center text-gray-500">
                      No branches found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}
