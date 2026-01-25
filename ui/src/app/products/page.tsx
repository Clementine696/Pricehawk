'use client';

import React, { useState, useEffect, Suspense, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { MainLayout } from '@/components/layout/MainLayout';
import { Search, RotateCcw, Download, ExternalLink, Loader2, ChevronDown, X, Check, TrendingUp, TrendingDown } from 'lucide-react';
import { apiFetch } from '@/lib/api';
import { trackExport, trackSearch, trackFilter } from '@/lib/analytics';

// Multi-select dropdown component with search
function MultiSelect({
  options,
  selected,
  onChange,
  placeholder,
  className = '',
}: {
  options: string[];
  selected: string[];
  onChange: (selected: string[]) => void;
  placeholder: string;
  className?: string;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Close dropdown when clicking outside
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

  // Focus search input when dropdown opens
  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isOpen]);

  const toggleOption = (option: string) => {
    if (selected.includes(option)) {
      onChange(selected.filter(s => s !== option));
    } else {
      onChange([...selected, option]);
    }
  };

  const clearAll = (e: React.MouseEvent) => {
    e.stopPropagation();
    onChange([]);
  };

  // Filter options based on search term
  const filteredOptions = options.filter(option =>
    option.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent bg-white text-left flex items-center justify-between gap-2"
      >
        <span className={`truncate ${selected.length === 0 ? 'text-gray-500' : 'text-gray-900'}`}>
          {selected.length === 0
            ? placeholder
            : selected.length === 1
            ? selected[0]
            : `${selected.length} selected`}
        </span>
        <div className="flex items-center gap-1 flex-shrink-0">
          {selected.length > 0 && (
            <button
              onClick={clearAll}
              className="p-0.5 hover:bg-gray-200 rounded"
            >
              <X className="w-3.5 h-3.5 text-gray-500" />
            </button>
          )}
          <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </div>
      </button>

      {isOpen && (
        <div className="absolute z-50 mt-1 w-full bg-white border border-gray-300 rounded-lg shadow-lg">
          {/* Search input */}
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
          {/* Options list */}
          <div className="max-h-48 overflow-auto">
            {filteredOptions.length === 0 ? (
              <div className="px-4 py-2 text-gray-500 text-sm">No options found</div>
            ) : (
              filteredOptions.map((option) => (
                <button
                  key={option}
                  type="button"
                  onClick={() => toggleOption(option)}
                  className="w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center gap-2"
                >
                  <div className={`w-4 h-4 border rounded flex items-center justify-center flex-shrink-0 ${
                    selected.includes(option)
                      ? 'bg-cyan-500 border-cyan-500'
                      : 'border-gray-300'
                  }`}>
                    {selected.includes(option) && <Check className="w-3 h-3 text-white" />}
                  </div>
                  <span className="text-sm text-gray-900 truncate">{option}</span>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// Single-select dropdown component with same styling as MultiSelect
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

  // Close dropdown when clicking outside
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

  const handleSelect = (optionValue: string) => {
    onChange(optionValue);
    setIsOpen(false);
  };

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    onChange('');
  };

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
            <button
              onClick={handleClear}
              className="p-0.5 hover:bg-gray-200 rounded"
            >
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
              onClick={() => handleSelect(option.value)}
              className={`w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center justify-between ${
                option.value === value ? 'bg-cyan-50' : ''
              }`}
            >
              <span className="text-sm text-gray-900 truncate">{option.label}</span>
              {option.value === value && <Check className="w-4 h-4 text-cyan-500 flex-shrink-0" />}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

interface PriceChange {
  old_price: number;
  change: number;
  change_pct: number;
  direction: 'up' | 'down';
}

interface RetailerPrice {
  price: number | null;
  link: string | null;
  verified?: boolean;
  price_change?: PriceChange | null;
}

interface Product {
  product_id: number;
  sku: string;
  name: string;
  brand: string | null;
  category: string | null;
  base_price: number | null;
  base_link: string | null;
  base_price_change?: PriceChange | null;
  status: 'cheapest' | 'same' | 'higher' | null;
  retailer_prices: Record<string, RetailerPrice>;
  is_verified: boolean;
}

interface Retailer {
  retailer_id: number;
  name: string;
}

const RETAILER_ORDER = ['Thai Watsadu', 'HomePro', 'MegaHome', 'Do Home', 'Boonthavorn', 'Global House'];

// Map alternative retailer names to the canonical name used in RETAILER_ORDER
const RETAILER_NAME_ALIASES: Record<string, string> = {
  'Mega Home': 'MegaHome',
  'megahome': 'MegaHome',
  'DoHome': 'Do Home',
  'GlobalHouse': 'Global House',
  'Home Pro': 'HomePro',
};

// Get retailer price data, checking both canonical name and aliases
const getRetailerPrice = (retailerPrices: Record<string, RetailerPrice> | undefined, retailerName: string): RetailerPrice | undefined => {
  if (!retailerPrices) return undefined;
  // Try canonical name first
  if (retailerPrices[retailerName]) return retailerPrices[retailerName];
  // Try to find by alias (reverse lookup)
  for (const [alias, canonical] of Object.entries(RETAILER_NAME_ALIASES)) {
    if (canonical === retailerName && retailerPrices[alias]) {
      return retailerPrices[alias];
    }
  }
  return undefined;
};

function ProductsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [products, setProducts] = useState<Product[]>([]);
  const [retailers, setRetailers] = useState<Retailer[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [brands, setBrands] = useState<string[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize state from URL params
  const [search, setSearch] = useState(searchParams.get('search') || '');
  // Category and brand are now arrays for multi-select
  const [selectedCategories, setSelectedCategories] = useState<string[]>(
    searchParams.get('category')?.split(',').filter(Boolean) || []
  );
  const [selectedBrands, setSelectedBrands] = useState<string[]>(
    searchParams.get('brand')?.split(',').filter(Boolean) || []
  );
  const [verificationFilter, setVerificationFilter] = useState(searchParams.get('verified') || '');
  const [retailerFilter, setRetailerFilter] = useState(searchParams.get('retailer') || '');
  const [page, setPage] = useState(Number(searchParams.get('page')) || 1);
  const [isExporting, setIsExporting] = useState(false);
  const pageSize = 10;

  // Retailer options for filter (excluding Thai Watsadu which is the base)
  const RETAILER_FILTER_OPTIONS = [
    { id: 'hp', name: 'HomePro' },
    { id: 'mgh', name: 'MegaHome' },
    { id: 'dh', name: 'DoHome' },
    { id: 'btv', name: 'Boonthavorn' },
    { id: 'gbh', name: 'Global House' },
  ];

  // Update URL when filters change
  const updateURL = (newParams: Record<string, string | number | string[]>) => {
    const params = new URLSearchParams();
    const allParams: Record<string, string | number | string[]> = {
      search,
      category: selectedCategories.join(','),
      brand: selectedBrands.join(','),
      verified: verificationFilter,
      retailer: retailerFilter,
      page,
      ...newParams
    };

    Object.entries(allParams).forEach(([key, value]) => {
      const strValue = Array.isArray(value) ? value.join(',') : String(value);
      if (strValue && strValue !== '' && !(key === 'page' && strValue === '1')) {
        params.set(key, strValue);
      }
    });

    const queryString = params.toString();
    router.push(queryString ? `?${queryString}` : '/products', { scroll: false });
  };

  useEffect(() => {
    fetchProducts();
  }, [page, search, selectedCategories, selectedBrands, verificationFilter, retailerFilter]);

  const fetchProducts = async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        pageSize: pageSize.toString(),
      });
      if (search) params.append('search', search);
      if (selectedCategories.length > 0) params.append('category', selectedCategories.join(','));
      if (selectedBrands.length > 0) params.append('brand', selectedBrands.join(','));
      if (verificationFilter) params.append('verified', verificationFilter);
      if (retailerFilter) params.append('retailer', retailerFilter);


      const response = await apiFetch(`/api/products?${params}`);
      if (!response.ok) throw new Error('Failed to fetch products');
      const data = await response.json();

      setProducts(data.products || []);
      setRetailers(data.retailers || []);
      setCategories(data.categories || []);
      setBrands(data.brands || []);
      setTotal(data.total || 0);
    } catch (error) {
      console.error('Error fetching products:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = () => {
    setPage(1);
    updateURL({ search, page: 1 });
    fetchProducts();
    // Track search event
    if (search) {
      trackSearch(search);
    }
  };

  const handleReset = () => {
    setSearch('');
    setSelectedCategories([]);
    setSelectedBrands([]);
    setVerificationFilter('');
    setRetailerFilter('');
    // setWatchedOnly(false);
    setPage(1);
    router.push('/products', { scroll: false });
    // Don't call fetchProducts() here - the useEffect will trigger it when state changes
  };

  const handleCategoryChange = (newCategories: string[]) => {
    setSelectedCategories(newCategories);
    setPage(1);
    updateURL({ category: newCategories.join(','), page: 1 });
    // Track filter usage
    trackFilter('category', newCategories.join(', '));
  };

  const handleBrandChange = (newBrands: string[]) => {
    setSelectedBrands(newBrands);
    setPage(1);
    updateURL({ brand: newBrands.join(','), page: 1 });
    // Track filter usage
    trackFilter('brand', newBrands.join(', '));
  };

  const handleFilterChange = (filterName: string, value: string) => {
    const setters: Record<string, (v: string) => void> = {
      verified: setVerificationFilter,
      retailer: setRetailerFilter,
    };
    setters[filterName]?.(value);
    setPage(1);
    updateURL({ [filterName]: value, page: 1 });
    // Track filter usage
    if (value) {
      trackFilter(filterName, value);
    }
  };

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
    updateURL({ page: newPage });
  };

  const handleExport = async () => {
    setIsExporting(true);
    try {
      const params = new URLSearchParams();
      if (search) params.append('search', search);
      if (selectedCategories.length > 0) params.append('category', selectedCategories.join(','));
      if (selectedBrands.length > 0) params.append('brand', selectedBrands.join(','));
      if (verificationFilter) params.append('verified', verificationFilter);
      if (retailerFilter) params.append('retailer', retailerFilter);

      const response = await apiFetch(`/api/products/export?${params}`);
      if (!response.ok) {
        throw new Error('Failed to export products');
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
      link.download = `products_export_${timestamp}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      // Track export event
      trackExport('products_xlsx', products.length);
    } catch (error) {
      console.error('Error exporting products:', error);
    } finally {
      setIsExporting(false);
    }
  };

  const formatPrice = (price: number | null) => {
    if (price === null) return '-';
    return `฿${price.toLocaleString()}`;
  };

  // Get price comparison category for coloring
  const getPriceCategory = (price: number | null, allPrices: (number | null)[]): 'cheapest' | 'same' | 'higher' | null => {
    if (price === null) return null;
    const validPrices = allPrices.filter((p): p is number => p !== null && p > 0);
    if (validPrices.length === 0) return null;

    const minPrice = Math.min(...validPrices);
    const maxPrice = Math.max(...validPrices);

    if (price === minPrice && minPrice === maxPrice) return 'same';
    if (price === minPrice) return 'cheapest';
    if (price > minPrice) return 'higher';
    return null;
  };

  const getPriceColorClass = (category: 'cheapest' | 'same' | 'higher' | null): string => {
    switch (category) {
      case 'cheapest': return 'text-green-600 font-semibold';
      case 'higher': return 'text-red-600';
      case 'same': return 'text-gray-500';
      default: return 'text-cyan-600';
    }
  };

  const PriceChangeIndicator = ({ change }: { change: PriceChange | null | undefined }) => {
    if (!change) return null;
    const isDown = change.direction === 'down';
    return (
      <span
        className={`inline-flex items-center text-xs ml-1 ${isDown ? 'text-green-600' : 'text-red-500'}`}
        title={`Was ฿${change.old_price.toLocaleString()} (${change.change_pct > 0 ? '+' : ''}${change.change_pct}%)`}
      >
        {isDown ? (
          <TrendingDown className="w-3 h-3" />
        ) : (
          <TrendingUp className="w-3 h-3" />
        )}
      </span>
    );
  };

  const getStatusBadge = (status: string | null) => {
    if (!status) {
      return (
        <span className="px-2 py-1 rounded text-xs font-medium bg-gray-200 text-gray-600">
          No Competitor
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
      <span className={`px-2 py-1 rounded text-xs font-medium ${styles[status]}`}>
        {labels[status]}
      </span>
    );
  };

  // Get ordered retailers excluding Thai Watsadu (base)
  const otherRetailers = RETAILER_ORDER.filter(name => name !== 'Thai Watsadu');

  const totalPages = Math.ceil(total / pageSize);
  const startItem = (page - 1) * pageSize + 1;
  const endItem = Math.min(page * pageSize, total);

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Products</h1>
          <p className="text-gray-600 mt-1">Compare prices across retailers</p>
        </div>

        {/* Search & Filter */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Search & Filter</h2>
          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search by name, SKU or brand..."
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
              className="w-[150px]"
            />
            <SingleSelect
              options={[
                { value: 'true', label: 'Verified' },
                { value: 'false', label: 'Unverified' },
              ]}
              value={verificationFilter}
              onChange={(value) => handleFilterChange('verified', value)}
              placeholder="All Status"
              className="w-[140px]"
            />
            <SingleSelect
              options={RETAILER_FILTER_OPTIONS.map(r => ({ value: r.id, label: r.name }))}
              value={retailerFilter}
              onChange={(value) => handleFilterChange('retailer', value)}
              placeholder="All Retailers"
              className="w-[150px]"
            />
            <button
              onClick={handleReset}
              className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <RotateCcw className="w-4 h-4" />
              Reset
            </button>
            <button
              onClick={handleExport}
              disabled={isExporting}
              className="flex items-center gap-2 px-4 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isExporting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Exporting...
                </>
              ) : (
                <>
                  <Download className="w-4 h-4" />
                  Export
                </>
              )}
            </button>
          </div>
        </div>

        {/* Price Comparison Table */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Price Comparison</h2>
          </div>

          {isLoading ? (
            <div className="p-12 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-500 mx-auto"></div>
              <p className="mt-2 text-gray-500">Loading products...</p>
            </div>
          ) : products.length === 0 ? (
            <div className="p-12 text-center text-gray-500">
              No products found
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full table-fixed min-w-[1400px]">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="w-[50px] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">No.</th>
                      <th className="w-[100px] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">SKU</th>
                      <th className="w-[280px] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product Name</th>
                      <th className="w-[100px] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Brand</th>
                      <th className="w-[120px] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                      <th className="w-[100px] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                      <th className="w-[90px] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Review</th>
                      <th className="w-[110px] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Thai Watsadu</th>
                      {otherRetailers.map((retailer) => (
                        <th key={retailer} className="w-[110px] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          {retailer}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {products.map((product, index) => {
                      // Collect all prices for comparison
                      const allPrices = [
                        product.base_price,
                        ...otherRetailers.map(r => getRetailerPrice(product.retailer_prices, r)?.price ?? null)
                      ];

                      return (
                        <tr
                          key={product.product_id}
                          onClick={() => router.push(`/products/${product.product_id}`)}
                          className="hover:bg-gray-50 cursor-pointer transition-colors h-10"
                        >
                          <td className="px-4 py-2 text-sm text-gray-500 text-center whitespace-nowrap">
                            {startItem + index}
                          </td>
                          <td className="px-4 py-2 text-sm text-gray-900 whitespace-nowrap">
                            {product.sku}
                          </td>
                          <td className="px-4 py-2 text-sm text-gray-900 max-w-xs truncate" title={product.name}>
                            {product.name}
                          </td>
                          <td className="px-4 py-2 text-sm text-gray-700 truncate" title={product.brand || '-'}>
                            {product.brand || '-'}
                          </td>
                          <td className="px-4 py-2 text-sm text-gray-700 truncate" title={product.category || '-'}>
                            {product.category || '-'}
                          </td>
                          <td className="px-4 py-2 whitespace-nowrap">
                            {getStatusBadge(product.status)}
                          </td>
                          <td className="px-4 py-2 whitespace-nowrap">
                            {product.is_verified ? (
                              <span className="px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-700">
                                Verified
                              </span>
                            ) : (
                              <span className="px-2 py-1 rounded text-xs font-medium bg-yellow-100 text-yellow-700">
                                Unverified
                              </span>
                            )}
                          </td>
                          <td className="px-4 py-2 text-sm whitespace-nowrap">
                            {product.base_price ? (
                              <span className="inline-flex items-center">
                                <a
                                  href={product.base_link || '#'}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  onClick={(e) => e.stopPropagation()}
                                  className={`inline-flex items-center gap-1 hover:underline ${getPriceColorClass(getPriceCategory(product.base_price, allPrices))}`}
                                >
                                  {formatPrice(product.base_price)}
                                  <ExternalLink className="w-3 h-3" />
                                </a>
                                <PriceChangeIndicator change={product.base_price_change} />
                              </span>
                            ) : <span className="text-gray-400">-</span>}
                          </td>
                          {otherRetailers.map((retailer) => {
                            const priceData = getRetailerPrice(product.retailer_prices, retailer);
                            const priceCategory = getPriceCategory(priceData?.price ?? null, allPrices);
                            const isUnverified = priceData?.price && priceData?.verified === false;
                            return (
                              <td key={retailer} className="px-4 py-2 text-sm whitespace-nowrap">
                                {priceData?.price ? (
                                  <span className="inline-flex items-center">
                                    <a
                                      href={priceData.link || '#'}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      onClick={(e) => e.stopPropagation()}
                                      className={`inline-flex items-center gap-1 hover:underline ${isUnverified ? 'italic opacity-70' : ''} ${getPriceColorClass(priceCategory)}`}
                                      title={isUnverified ? 'Unverified match - click to review' : undefined}
                                    >
                                      {formatPrice(priceData.price)}
                                      {isUnverified && <span className="text-yellow-500">?</span>}
                                      <ExternalLink className="w-3 h-3" />
                                    </a>
                                    <PriceChangeIndicator change={priceData.price_change} />
                                  </span>
                                ) : <span className="text-gray-400">-</span>}
                              </td>
                            );
                          })}
                        </tr>
                      );
                    })}
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
                    onClick={() => handlePageChange(Math.max(1, page - 1))}
                    disabled={page === 1}
                    className="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <span className="px-3 py-1 text-sm text-gray-600">
                    Page {page} of {totalPages || 1}
                  </span>
                  <button
                    onClick={() => handlePageChange(Math.min(totalPages, page + 1))}
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

export default function ProductsPage() {
  return (
    <Suspense fallback={
      <MainLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <Loader2 className="w-12 h-12 animate-spin text-cyan-500 mx-auto" />
            <p className="mt-4 text-gray-600">Loading products...</p>
          </div>
        </div>
      </MainLayout>
    }>
      <ProductsContent />
    </Suspense>
  );
}
