'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { MainLayout } from '@/components/layout/MainLayout';
import { Search, RotateCcw, Download, ExternalLink, Loader2 } from 'lucide-react';
import { apiFetch } from '@/lib/api';

interface RetailerPrice {
  price: number | null;
  link: string | null;
}

interface Product {
  product_id: number;
  sku: string;
  name: string;
  brand: string | null;
  category: string | null;
  base_price: number | null;
  base_link: string | null;
  status: 'cheapest' | 'same' | 'higher' | null;
  retailer_prices: Record<string, RetailerPrice>;
}

interface Retailer {
  retailer_id: number;
  name: string;
}

const RETAILER_ORDER = ['Thai Watsadu', 'HomePro', 'Do Home', 'Boonthavorn', 'Global House'];

export default function ProductsPage() {
  const router = useRouter();
  const [products, setProducts] = useState<Product[]>([]);
  const [retailers, setRetailers] = useState<Retailer[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [brands, setBrands] = useState<string[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [brand, setBrand] = useState('');
  const [page, setPage] = useState(1);
  const [isExporting, setIsExporting] = useState(false);
  const pageSize = 10;

  useEffect(() => {
    fetchProducts();
  }, [page, category, brand]);

  const fetchProducts = async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        pageSize: pageSize.toString(),
      });
      if (search) params.append('search', search);
      if (category) params.append('category', category);
      if (brand) params.append('brand', brand);

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
    fetchProducts();
  };

  const handleReset = () => {
    setSearch('');
    setCategory('');
    setBrand('');
    setPage(1);
    fetchProducts();
  };

  const handleExport = async () => {
    setIsExporting(true);
    try {
      const params = new URLSearchParams();
      if (search) params.append('search', search);
      if (category) params.append('category', category);
      if (brand) params.append('brand', brand);

      const response = await apiFetch(`/api/products/export?${params}`);
      if (!response.ok) {
        throw new Error('Failed to export products');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'products_export.csv';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
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

  const getStatusBadge = (status: string | null) => {
    if (!status) return null;
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
            <select
              value={category}
              onChange={(e) => { setCategory(e.target.value); setPage(1); }}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent bg-white"
            >
              <option value="">All Categories</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
            <select
              value={brand}
              onChange={(e) => { setBrand(e.target.value); setPage(1); }}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent bg-white"
            >
              <option value="">All Brands</option>
              {brands.map((b) => (
                <option key={b} value={b}>{b}</option>
              ))}
            </select>
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
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">No.</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">SKU</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product Name</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Brand</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Thai Watsadu</th>
                      {otherRetailers.map((retailer) => (
                        <th key={retailer} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
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
                        ...otherRetailers.map(r => product.retailer_prices?.[r]?.price ?? null)
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
                          <td className="px-4 py-2 text-sm font-mono text-gray-900 whitespace-nowrap">
                            {product.sku}
                          </td>
                          <td className="px-4 py-2 text-sm text-gray-900 max-w-xs truncate" title={product.name}>
                            {product.name}
                          </td>
                          <td className="px-4 py-2 text-sm text-gray-700 whitespace-nowrap">
                            {product.brand || '-'}
                          </td>
                          <td className="px-4 py-2 text-sm text-gray-700 whitespace-nowrap">
                            {product.category || '-'}
                          </td>
                          <td className="px-4 py-2 whitespace-nowrap">
                            {getStatusBadge(product.status)}
                          </td>
                          <td className="px-4 py-2 text-sm whitespace-nowrap">
                            {product.base_price ? (
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
                            ) : <span className="text-gray-400">-</span>}
                          </td>
                          {otherRetailers.map((retailer) => {
                            const priceData = product.retailer_prices?.[retailer];
                            const priceCategory = getPriceCategory(priceData?.price ?? null, allPrices);
                            return (
                              <td key={retailer} className="px-4 py-2 text-sm whitespace-nowrap">
                                {priceData?.price ? (
                                  <a
                                    href={priceData.link || '#'}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    onClick={(e) => e.stopPropagation()}
                                    className={`inline-flex items-center gap-1 hover:underline ${getPriceColorClass(priceCategory)}`}
                                  >
                                    {formatPrice(priceData.price)}
                                    <ExternalLink className="w-3 h-3" />
                                  </a>
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
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <span className="px-3 py-1 text-sm text-gray-600">
                    Page {page} of {totalPages || 1}
                  </span>
                  <button
                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
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
