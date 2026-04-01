'use client';

import { useState, useEffect, Suspense, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { MainLayout } from '@/components/layout/MainLayout';
import { Search, RotateCcw, Settings, Download, Loader2, ChevronDown } from 'lucide-react';
import Link from 'next/link';
import { apiFetch } from '@/lib/api';
import { MultiSelect } from '@/components/ui/MultiSelect';
import { Button } from '@/components/ui/Button';

interface LocationProduct {
  twd_sku: string;
  twd_name: string;
  twd_price: number | null;
  brand: string | null;
  category: string | null;
  sdept: string | null;
  gbh_sku: string;
  gbh_name: string;
  gbh_url: string;
  min_price: number | null;
  max_price: number | null;
  avg_price: number | null;
  branch_count: number;
  total_branches: number;
  price_status: 'has_cheaper' | 'all_higher' | 'same' | 'unknown';
}


// ── SingleSelect ─────────────────────────────────────────────────────────────
function SingleSelect({
  options,
  value,
  onChange,
  placeholder,
  className = '',
}: {
  options: { value: string; label: string }[];
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  className?: string;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const selectedOption = options.find(o => o.value === value);

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent bg-white text-left flex items-center justify-between gap-2"
      >
        <span className={`truncate ${!value ? 'text-gray-500' : 'text-gray-900'}`}>
          {selectedOption?.label || placeholder}
        </span>
        <div className="flex items-center gap-1 flex-shrink-0">
          {value && (
            <button onClick={(e) => { e.stopPropagation(); onChange(''); }} className="p-0.5 hover:bg-gray-200 rounded">
              <X className="w-3.5 h-3.5 text-gray-500" />
            </button>
          )}
          <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </div>
      </button>
      {isOpen && (
        <div className="absolute z-50 mt-1 w-full bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-auto">
          {options.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => { onChange(option.value); setIsOpen(false); }}
              className={`w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center justify-between ${option.value === value ? 'bg-cyan-50' : ''}`}
            >
              <span className="text-sm text-gray-900">{option.label}</span>
              {option.value === value && <Check className="w-4 h-4 text-cyan-500 flex-shrink-0" />}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Main content ─────────────────────────────────────────────────────────────
function PriceByLocationContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [products, setProducts] = useState<LocationProduct[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState(searchParams.get('search') || '');
  const [selectedWatchlistGroups, setSelectedWatchlistGroups] = useState<string[]>(
    searchParams.get('watchlist_group') ? searchParams.get('watchlist_group')!.split(',') : []
  );
  const [selectedBrands, setSelectedBrands] = useState<string[]>(
    searchParams.get('brand') ? searchParams.get('brand')!.split(',') : []
  );
  const [priceStatus, setPriceStatus] = useState(searchParams.get('price_status') || '');
  const [page, setPage] = useState(Number(searchParams.get('page') || 1));
  const [pageSize] = useState(50);
  const [total, setTotal] = useState(0);
  const [watchlistGroups, setWatchlistGroups] = useState<string[]>([]);
  const [brands, setBrands] = useState<string[]>([]);

  useEffect(() => {
    fetchData();
  }, [page, selectedWatchlistGroups, selectedBrands, priceStatus]);

  const buildParams = () => {
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
    if (search) params.set('search', search);
    if (selectedWatchlistGroups.length > 0) params.set('watchlist_group', selectedWatchlistGroups.join(','));
    if (selectedBrands.length > 0) params.set('brand', selectedBrands.join(','));
    if (priceStatus) params.set('price_status', priceStatus);
    return params;
  };

  const fetchData = async () => {
    setIsLoading(true);
    setError('');
    try {
      const response = await apiFetch(`/api/location-prices/summary?${buildParams()}`);
      if (!response.ok) throw new Error('Failed to fetch location prices');
      const result = await response.json();
      setProducts(result.products);
      setTotal(result.total);
      if (result.watchlist_groups) setWatchlistGroups(result.watchlist_groups);
      if (result.brands) setBrands(result.brands);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = () => {
    setPage(1);
    fetchData();
  };

  const handleReset = () => {
    setSearch('');
    setSelectedWatchlistGroups([]);
    setSelectedBrands([]);
    setPriceStatus('');
    setPage(1);
    router.push('/price-by-location');
  };

  const handleWatchlistGroupChange = (vals: string[]) => {
    setSelectedWatchlistGroups(vals);
    setPage(1);
  };

  const handleBrandChange = (vals: string[]) => {
    setSelectedBrands(vals);
    setPage(1);
  };

  const totalPages = Math.ceil(total / pageSize);
  const startItem = (page - 1) * pageSize + 1;
  const endItem = Math.min(page * pageSize, total);

  const formatPrice = (price: number | null) => {
    if (price === null || price === undefined) return '-';
    return `฿${price.toLocaleString('th-TH', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
  };

  // Compare TWD price to GlobalHouse min/max prices
  const getPriceCategory = (twdPrice: number | null, minPrice: number | null, maxPrice: number | null): 'cheapest' | 'same' | 'higher' | null => {
    if (twdPrice === null) return null;
    if (minPrice === null || maxPrice === null) return null;

    // If all prices are the same
    if (twdPrice === minPrice && twdPrice === maxPrice) return 'same';
    
    // If TWD is cheapest (equal to or less than minimum)
    if (twdPrice <= minPrice) return 'cheapest';
    
    // If TWD is higher than minimum
    if (twdPrice > minPrice) return 'higher';
    
    return null;
  };

  const getPriceStatusBadge = (twdPrice: number | null, minPrice: number | null, maxPrice: number | null) => {
    const category = getPriceCategory(twdPrice, minPrice, maxPrice);
    
    if (category === null) {
      return (
        <span className="px-2 py-1 rounded text-xs font-medium bg-gray-200 text-gray-600">
          No Data
        </span>
      );
    }

    const styles: Record<string, string> = {
      cheapest: 'bg-emerald-500 text-white',
      same: 'bg-gray-400 text-white',
      higher: 'bg-amber-500 text-white',
    };
    const labels: Record<string, string> = {
      cheapest: 'Cheapest',
      same: 'Same',
      higher: 'Higher',
    };

    return (
      <span className={`px-2 py-1 rounded text-xs font-medium ${styles[category]}`}>
        {labels[category]}
      </span>
    );
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Price by Location</h1>
            <p className="text-gray-600 mt-1">Compare price by location branch</p>
          </div>
          <div className="flex gap-3">
            <Button variant="outline" onClick={fetchData} icon={<RotateCcw className="w-4 h-4" />}>Refresh</Button>
            <Link
              href="/price-by-location/settings"
              className="flex items-center gap-2 px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 transition-colors"
            >
              <Settings className="w-4 h-4" />
              Settings
            </Link>
          </div>
        </div>

        {/* Search & Filter */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Search & Filter</h2>
          <div className="flex flex-col lg:flex-row gap-4">
            {/* Search input – supports multiple SKUs */}
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search by name, SKU, brand or paste multiple SKUs..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
              />
            </div>

            <MultiSelect
              options={watchlistGroups}
              selected={selectedWatchlistGroups}
              onChange={handleWatchlistGroupChange}
              placeholder="All Watchlists"
              className="w-[200px]"
            />

            <MultiSelect
              options={brands}
              selected={selectedBrands}
              onChange={handleBrandChange}
              placeholder="All Brands"
              className="w-[160px]"
            />

            <SingleSelect
              options={[
                { value: 'cheapest', label: 'Cheapest' },
                { value: 'same', label: 'Same' },
                { value: 'higher', label: 'Higher' },
              ]}
              value={priceStatus}
              onChange={(val) => { setPriceStatus(val); setPage(1); }}
              placeholder="All Status"
              className="w-[140px]"
            />

            <Button variant="outline" onClick={handleReset} icon={<RotateCcw className="w-4 h-4" />}>Reset</Button>

            <Button
              variant="primary"
              icon={<Download className="w-4 h-4" />}
              onClick={async () => {
                const params = new URLSearchParams();
                if (search) params.set('search', search);
                if (selectedWatchlistGroups.length > 0) params.set('watchlist_group', selectedWatchlistGroups.join(','));
                if (selectedBrands.length > 0) params.set('brand', selectedBrands.join(','));
                if (priceStatus) params.set('price_status', priceStatus);
                const qs = params.toString();
                const res = await apiFetch(`/api/location-prices/export${qs ? `?${qs}` : ''}`);
                if (res.ok) {
                  const blob = await res.blob();
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `price_by_location_${new Date().toISOString().slice(0,10)}.xlsx`;
                  a.click();
                  URL.revokeObjectURL(url);
                }
              }}
            >
              Export
            </Button>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">{error}</div>
        )}

        {/* Table */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Products</h2>
          </div>

          {isLoading ? (
            <div className="p-12 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-500 mx-auto"></div>
              <p className="mt-2 text-gray-500">Loading products...</p>
            </div>
          ) : products.length === 0 ? (
            <div className="p-12 text-center text-gray-500">
              <p className="text-lg font-medium mb-2">No location price data yet</p>
              <p className="text-sm mb-6">Configure groups and locations in settings, then run the price updater service</p>
              <Link
                href="/price-by-location/settings"
                className="inline-flex items-center gap-2 px-6 py-3 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 transition-colors"
              >
                <Settings className="h-5 w-5" />
                Go to Settings
              </Link>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full table-fixed min-w-[1100px]">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="w-[50px] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">No.</th>
                      <th className="w-[100px] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">SKU</th>
                      <th className="w-[260px] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product Name</th>
                      <th className="w-[100px] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Brand</th>
                      <th className="w-[120px] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                      <th className="w-[110px] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">My Price</th>
                      <th className="w-[100px] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Min</th>
                      <th className="w-[100px] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Max</th>
                      <th className="w-[100px] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Avg</th>
                      <th className="w-[90px] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Branch</th>
                      <th className="w-[110px] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {products.map((product, index) => (
                      <tr
                        key={product.twd_sku}
                        onClick={() => window.open(`/price-by-location/${product.twd_sku}`, '_blank')}
                        className="hover:bg-gray-50 cursor-pointer transition-colors h-10"
                      >
                        <td className="px-4 py-2 text-sm text-gray-500 text-center whitespace-nowrap">
                          {startItem + index}
                        </td>
                        <td className="px-4 py-2 text-sm text-gray-900 whitespace-nowrap">
                          {product.twd_sku}
                        </td>
                        <td className="px-4 py-2 text-sm text-gray-900 truncate" title={product.twd_name}>
                          {product.twd_name}
                        </td>
                        <td className="px-4 py-2 text-sm text-gray-700 truncate" title={product.brand || '-'}>
                          {product.brand || '-'}
                        </td>
                        <td className="px-4 py-2 text-sm text-gray-700 truncate" title={product.category || '-'}>
                          {product.category || '-'}
                        </td>
                        <td className="px-4 py-2 text-sm text-gray-900 whitespace-nowrap">
                          {formatPrice(product.twd_price)}
                        </td>
                        <td className="px-4 py-2 text-sm whitespace-nowrap">
                          <span className="text-green-700 font-medium">{formatPrice(product.min_price)}</span>
                        </td>
                        <td className="px-4 py-2 text-sm whitespace-nowrap">
                          <span className="text-red-600 font-medium">{formatPrice(product.max_price)}</span>
                        </td>
                        <td className="px-4 py-2 text-sm text-gray-900 whitespace-nowrap">
                          {formatPrice(product.avg_price)}
                        </td>
                        <td className="px-4 py-2 text-sm text-gray-900 whitespace-nowrap">
                          {product.branch_count}/{product.total_branches}
                        </td>
                        <td className="px-4 py-2 whitespace-nowrap">
                          {getPriceStatusBadge(product.twd_price, product.min_price, product.max_price)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
                <div className="text-sm text-gray-500">
                  Showing {startItem} to {endItem} of {total} products
                </div>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" onClick={() => setPage(Math.max(1, page - 1))} disabled={page === 1}>Previous</Button>
                  <span className="px-3 py-1 text-sm text-gray-600">
                    Page {page} of {totalPages || 1}
                  </span>
                  <Button size="sm" variant="outline" onClick={() => setPage(Math.min(totalPages, page + 1))} disabled={page >= totalPages}>Next</Button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </MainLayout>
  );
}

export default function PriceByLocationPage() {
  return (
    <Suspense fallback={
      <MainLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <Loader2 className="w-12 h-12 animate-spin text-cyan-500 mx-auto" />
            <p className="mt-4 text-gray-600">Loading...</p>
          </div>
        </div>
      </MainLayout>
    }>
      <PriceByLocationContent />
    </Suspense>
  );
}
