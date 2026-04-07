'use client';

import React, { useState, useEffect, Suspense, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { MainLayout } from '@/components/layout/MainLayout';
import { Search, RotateCcw, Download, ExternalLink, Loader2, ChevronDown, X } from 'lucide-react';
import { apiFetch } from '@/lib/api';
import { trackExport, trackSearch, trackFilter } from '@/lib/analytics';
import { MultiSelect } from '@/components/ui/MultiSelect';
import { Button } from '@/components/ui/Button';

// Single-select dropdown component
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
              className={`w-full px-4 py-2 text-left hover:bg-gray-50 ${
                option.value === value ? 'bg-cyan-50' : ''
              }`}
            >
              <span className="text-sm text-gray-900">{option.label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

interface Product {
  id: number;
  retailer_id: string;
  retailer_name: string;
  sku: string;
  barcode: string | null;
  name: string;
  name_en: string | null;
  brand: string | null;
  category_id: string | null;
  category_name: string | null;
  current_price: number | null;
  step_prices: any;
  url: string | null;
  image_url: string | null;
  is_active: boolean;
  match_count: number;
  verified_match_count: number;
  unverified_count: number;
  matched_price: number | null;
}

interface Retailer {
  retailer_id: string;
  name: string;
}

function ProductsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [products, setProducts] = useState<Product[]>([]);
  const [retailers, setRetailers] = useState<Retailer[]>([]);
  const [categories, setCategories] = useState<{ value: string; label: string }[]>([]);
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
  const [matchStatus, setMatchStatus] = useState(searchParams.get('match_status') || '');
  const [priceStatus, setPriceStatus] = useState(searchParams.get('price_status') || '');
  const [page, setPage] = useState(Number(searchParams.get('page')) || 1);
  const [isExporting, setIsExporting] = useState(false);
  const pageSize = 10;

  // Update URL when filters change
  const updateURL = (newParams: Record<string, string | number | string[]>) => {
    const params = new URLSearchParams();
    const allParams: Record<string, string | number | string[]> = {
      search,
      category: selectedCategories.join(','),
      brand: selectedBrands.join(','),
      match_status: matchStatus,
      price_status: priceStatus,
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
  }, [page, search, selectedCategories, selectedBrands, matchStatus, priceStatus]);

  const fetchProducts = async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      });
      
      if (search) params.append('search', search);
      if (selectedCategories.length > 0) params.append('category', selectedCategories.join(','));
      if (selectedBrands.length > 0) params.append('brand', selectedBrands.join(','));
      if (matchStatus) params.append('match_status', matchStatus);
      if (priceStatus) params.append('price_status', priceStatus);

      const response = await apiFetch(`/api/products?${params}`);
      if (!response.ok) throw new Error('Failed to fetch products');
      
      const data = await response.json();
      setProducts(data.products || []);
      setRetailers(data.retailers || []);
      
      // Transform categories to MultiSelect format
      const transformedCategories = (data.categories || []).map((cat: any) => ({
        value: cat.category_id,
        label: cat.category_name
      }));
      setCategories(transformedCategories);
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
    setMatchStatus('');
    setPriceStatus('');
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

  const handleMatchStatusChange = (value: string) => {
    setMatchStatus(value);
    setPage(1);
    updateURL({ match_status: value, page: 1 });
    // Track filter usage
    if (value) {
      trackFilter('match_status', value);
    }
  };

  const handlePriceStatusChange = (value: string) => {
    setPriceStatus(value);
    setPage(1);
    updateURL({ price_status: value, page: 1 });
    // Track filter usage
    if (value) {
      trackFilter('price_status', value);
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

  // Helper to determine status badge
  const getStatus = (product: Product) => {
    const allRejected = product.match_count > 0 && product.verified_match_count === 0 && product.unverified_count === 0;
    const hasVerifiedMatch = product.verified_match_count > 0;

    if (allRejected || !product.matched_price || !product.current_price) {
      return { label: 'No Match', color: 'bg-gray-100 text-gray-700' };
    }

    const myPrice = product.current_price;
    const matchedPrice = product.matched_price;

    if (myPrice < matchedPrice) {
      return { label: 'Lower', color: 'bg-green-100 text-green-700' };
    } else if (myPrice > matchedPrice) {
      return { label: 'Higher', color: 'bg-red-100 text-red-700' };
    } else {
      return { label: 'Same', color: 'bg-gray-100 text-gray-700' };
    }
  };

  // Helper to determine verification badge
  const getVerification = (product: Product) => {
    // No matches at all, or all rejected (no correct, no unverified pending)
    if (product.match_count === 0 || (product.verified_match_count === 0 && product.unverified_count === 0)) {
      return { label: 'No Match', color: 'bg-gray-100 text-gray-700' };
    }
    if (product.verified_match_count > 0) {
      return { label: 'Verified', color: 'bg-emerald-100 text-emerald-700' };
    }
    return { label: 'Unverified', color: 'bg-orange-100 text-orange-700' };
  };

  // Helper to get prices for display
  const getPrices = (product: Product) => {
    const allRejected = product.match_count > 0 && product.verified_match_count === 0 && product.unverified_count === 0;
    const isCfw = product.retailer_id === 'cfw';
    // Show matched_price if: correct match exists OR top unverified exists (backend handles fallback)
    // Don't show if all rejected
    const showMatchedPrice = !allRejected && product.matched_price != null;

    return {
      cfw: isCfw ? product.current_price : (showMatchedPrice ? product.matched_price : null),
      makro: !isCfw ? product.current_price : (showMatchedPrice ? product.matched_price : null),
      showCfwLink: isCfw,
      showMakroLink: !isCfw,
    };
  };

  // Calculate pagination info from backend total
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
                placeholder="Search by name, SKU, brand, or paste multiple SKUs..."
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
                { value: 'verified', label: 'Verified' },
                { value: 'unverified', label: 'Unverified' },
                { value: 'no_match', label: 'No Match' },
              ]}
              value={matchStatus}
              onChange={handleMatchStatusChange}
              placeholder="Match Status"
              className="w-[160px]"
            />
            <SingleSelect
              options={[
                { value: 'lower', label: 'Lower' },
                { value: 'higher', label: 'Higher' },
                { value: 'same', label: 'Same' },
                { value: 'no_match', label: 'No Match' },
              ]}
              value={priceStatus}
              onChange={handlePriceStatusChange}
              placeholder="Price Status"
              className="w-[160px]"
            />
            <Button variant="outline" onClick={handleReset} icon={<RotateCcw className="w-4 h-4" />}>
              Reset
            </Button>
            <Button
              variant="primary"
              onClick={handleExport}
              disabled={isExporting}
              loading={isExporting}
              icon={<Download className="w-4 h-4" />}
            >
              {isExporting ? 'Exporting...' : 'Export'}
            </Button>
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
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-16">No.</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32">SKU</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product Name</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32">Brand</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32">Category</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-24">Buyer ID</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32">Status</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-28">Verification</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32">CFW</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32">MAKRO</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 bg-white">
                    {products.map((product, index) => {
                      const status = getStatus(product);
                      const verification = getVerification(product);
                      const prices = getPrices(product);

                      return (
                        <tr key={product.id} className="hover:bg-gray-50 transition-colors">
                          <td className="px-4 py-3 text-sm text-gray-500 text-center">
                            {startItem + index}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-900 font-mono">
                            {product.sku || '-'}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-900">
                            <button
                              onClick={() => router.push(`/products/${product.sku}`)}
                              className="text-gray-900 hover:text-cyan-600 hover:underline text-left"
                            >
                              {product.name}
                            </button>
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-700">
                            {product.brand || '-'}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-700">
                            {product.category_name || '-'}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-700 text-center font-medium">
                            DF8
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap">
                            <span className={`px-2 py-1 rounded text-xs font-medium ${status.color}`}>
                              {status.label}
                            </span>
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap">
                            <span className={`px-2 py-1 rounded text-xs font-medium ${verification.color}`}>
                              {verification.label}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm whitespace-nowrap">
                            {prices.cfw ? (
                              <a
                                href={prices.showCfwLink ? product.url || '#' : '#'}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-1 text-gray-900 hover:underline hover:text-cyan-600"
                              >
                                {formatPrice(prices.cfw)}
                                {prices.showCfwLink && <ExternalLink className="w-3 h-3" />}
                              </a>
                            ) : (
                              <span className="text-gray-400">-</span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-sm whitespace-nowrap">
                            {prices.makro ? (
                              <a
                                href={prices.showMakroLink ? product.url || '#' : '#'}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-1 text-gray-900 hover:underline hover:text-cyan-600"
                              >
                                {formatPrice(prices.makro)}
                                {prices.showMakroLink && <ExternalLink className="w-3 h-3" />}
                              </a>
                            ) : (
                              <span className="text-gray-400">-</span>
                            )}
                          </td>
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
                  <Button size="sm" variant="outline" onClick={() => handlePageChange(Math.max(1, page - 1))} disabled={page === 1}>Previous</Button>
                  <span className="px-3 py-1 text-sm text-gray-600">Page {page} of {totalPages || 1}</span>
                  <Button size="sm" variant="outline" onClick={() => handlePageChange(Math.min(totalPages, page + 1))} disabled={page >= totalPages}>Next</Button>
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
