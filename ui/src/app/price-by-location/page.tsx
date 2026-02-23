'use client';

import { useState, useEffect, Suspense, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { MainLayout } from '@/components/layout/MainLayout';
import { Search, RotateCcw, Settings, Download, Loader2, ChevronDown, X, Check } from 'lucide-react';
import Link from 'next/link';
import { apiFetch } from '@/lib/api';

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

// ── MultiSelect (same as products page) ─────────────────────────────────────
function MultiSelect({
  options,
  selected,
  onChange,
  placeholder,
  className = '',
}: {
  options: string[] | { value: string; label: string }[];
  selected: string[];
  onChange: (selected: string[]) => void;
  placeholder: string;
  className?: string;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [dropdownWidth, setDropdownWidth] = useState<number | null>(null);
  const [dropdownHeight, setDropdownHeight] = useState(192);
  const containerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const resizeHandleCornerRef = useRef<HTMLDivElement>(null);

  const normalizedOptions = options.map(opt =>
    typeof opt === 'string' ? { value: opt, label: opt } : opt
  );

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchTerm('');
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    if (isOpen && searchInputRef.current) searchInputRef.current.focus();
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    const handleMouseMove = (e: MouseEvent) => {
      const containerRect = containerRef.current?.getBoundingClientRect();
      if (!containerRect) return;
      if (resizeHandleCornerRef.current?.dataset.dragging === 'true') {
        e.preventDefault();
        setDropdownWidth(Math.max(200, Math.min(800, e.clientX - containerRect.left)));
        setDropdownHeight(Math.max(100, Math.min(600, e.clientY - containerRect.top - 70)));
      }
    };
    const handleMouseUp = () => {
      if (resizeHandleCornerRef.current) resizeHandleCornerRef.current.dataset.dragging = 'false';
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isOpen]);

  const toggleOption = (value: string) => {
    onChange(selected.includes(value) ? selected.filter(s => s !== value) : [...selected, value]);
  };

  const clearAll = (e: React.MouseEvent) => { e.stopPropagation(); onChange([]); };

  const selectedLabels = selected.map(val => {
    const opt = normalizedOptions.find(o => o.value === val);
    return opt ? opt.label : val;
  });

  const filteredOptions = normalizedOptions.filter(o =>
    o.label.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent bg-white text-left flex items-center justify-between gap-2"
      >
        <span className={`truncate ${selected.length === 0 ? 'text-gray-500' : 'text-gray-900'}`}>
          {selected.length === 0 ? placeholder : selected.length === 1 ? selectedLabels[0] : `${selected.length} selected`}
        </span>
        <div className="flex items-center gap-1 flex-shrink-0">
          {selected.length > 0 && (
            <button onClick={clearAll} className="p-0.5 hover:bg-gray-200 rounded">
              <X className="w-3.5 h-3.5 text-gray-500" />
            </button>
          )}
          <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </div>
      </button>

      {isOpen && (
        <div
          className="absolute z-50 mt-1 bg-white border border-gray-300 rounded-lg shadow-lg flex flex-col"
          style={{ width: dropdownWidth ? `${dropdownWidth}px` : '100%', minWidth: '100%' }}
        >
          <div className="flex flex-1 min-h-0">
            <div className="flex-1 flex flex-col min-w-0">
              <div className="p-2 border-b border-gray-200">
                <div className="relative">
                  <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    ref={searchInputRef}
                    type="text"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="Search..."
                    className="w-full pl-8 pr-3 py-1.5 text-sm border border-gray-200 rounded focus:outline-none focus:ring-1 focus:ring-cyan-500"
                  />
                </div>
              </div>
              <div className="overflow-auto" style={{ height: `${dropdownHeight}px` }}>
                {filteredOptions.length === 0 ? (
                  <div className="px-4 py-2 text-gray-500 text-sm">No options found</div>
                ) : (
                  filteredOptions.map((option) => (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() => toggleOption(option.value)}
                      className="w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center gap-2"
                    >
                      <div className={`w-4 h-4 border rounded flex items-center justify-center flex-shrink-0 ${
                        selected.includes(option.value) ? 'bg-cyan-500 border-cyan-500' : 'border-gray-300'
                      }`}>
                        {selected.includes(option.value) && <Check className="w-3 h-3 text-white" />}
                      </div>
                      <span className="text-sm text-gray-900 break-words">{option.label}</span>
                    </button>
                  ))
                )}
              </div>
            </div>
          </div>
          <div
            ref={resizeHandleCornerRef}
            onMouseDown={(e) => {
              e.preventDefault();
              if (resizeHandleCornerRef.current) {
                resizeHandleCornerRef.current.dataset.dragging = 'true';
                document.body.style.cursor = 'nwse-resize';
                document.body.style.userSelect = 'none';
              }
            }}
            className="absolute bottom-0 right-0 w-4 h-4 cursor-nwse-resize hover:bg-cyan-100 rounded-bl-lg flex items-center justify-center group"
          >
            <div className="w-3 h-3 border-r-2 border-b-2 border-gray-400 group-hover:border-cyan-500"></div>
          </div>
        </div>
      )}
    </div>
  );
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
  const [selectedCategories, setSelectedCategories] = useState<string[]>(
    searchParams.get('category') ? searchParams.get('category')!.split(',') : []
  );
  const [selectedBrands, setSelectedBrands] = useState<string[]>(
    searchParams.get('brand') ? searchParams.get('brand')!.split(',') : []
  );
  const [priceStatus, setPriceStatus] = useState(searchParams.get('price_status') || '');
  const [page, setPage] = useState(Number(searchParams.get('page') || 1));
  const [pageSize] = useState(50);
  const [total, setTotal] = useState(0);
  const [categories, setCategories] = useState<string[]>([]);
  const [brands, setBrands] = useState<string[]>([]);

  useEffect(() => {
    fetchData();
  }, [page, selectedCategories, selectedBrands, priceStatus]);

  const buildParams = () => {
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
    if (search) params.set('search', search);
    if (selectedCategories.length > 0) params.set('category', selectedCategories.join(','));
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
      if (result.categories) setCategories(result.categories);
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
    setSelectedCategories([]);
    setSelectedBrands([]);
    setPriceStatus('');
    setPage(1);
    router.push('/price-by-location');
  };

  const handleCategoryChange = (vals: string[]) => {
    setSelectedCategories(vals);
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

  const getPriceStatusBadge = (status: LocationProduct['price_status']) => {
    switch (status) {
      case 'has_cheaper':
        return <span className="px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-700">Has Cheaper</span>;
      case 'all_higher':
        return <span className="px-2 py-1 rounded text-xs font-medium bg-red-100 text-red-600">All Higher</span>;
      case 'same':
        return <span className="px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-600">Same</span>;
      default:
        return <span className="text-gray-400">-</span>;
    }
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Price by Location</h1>
            <p className="text-gray-600 mt-1">Compare GlobalHouse branch prices against Thai Watsadu</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={fetchData}
              className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <RotateCcw className="w-4 h-4" />
              Refresh
            </button>
            <button
              onClick={async () => {
                const params = new URLSearchParams();
                if (search) params.set('search', search);
                if (selectedCategories.length > 0) params.set('category', selectedCategories.join(','));
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
              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              <Download className="w-4 h-4" />
              Export
            </button>
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
              options={categories}
              selected={selectedCategories}
              onChange={handleCategoryChange}
              placeholder="All Categories"
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
                { value: 'has_cheaper', label: 'Has Cheaper' },
                { value: 'all_higher', label: 'All Higher' },
                { value: 'same', label: 'Same' },
              ]}
              value={priceStatus}
              onChange={(val) => { setPriceStatus(val); setPage(1); }}
              placeholder="All Status"
              className="w-[140px]"
            />

            <button
              onClick={handleSearch}
              className="px-4 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition-colors"
            >
              Search
            </button>

            <button
              onClick={handleReset}
              className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <RotateCcw className="w-4 h-4" />
              Reset
            </button>
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
                      <th className="w-[110px] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">TWD Price</th>
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
                          {getPriceStatusBadge(product.price_status)}
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
                  <button
                    onClick={() => setPage(Math.max(1, page - 1))}
                    disabled={page === 1}
                    className="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <span className="px-3 py-1 text-sm text-gray-600">
                    Page {page} of {totalPages || 1}
                  </span>
                  <button
                    onClick={() => setPage(Math.min(totalPages, page + 1))}
                    disabled={page >= totalPages}
                    className="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
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
