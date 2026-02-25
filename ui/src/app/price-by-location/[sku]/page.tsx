'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { MainLayout } from '@/components/layout/MainLayout';
import { ArrowLeft, MapPin, RotateCcw, Loader2, ExternalLink } from 'lucide-react';
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

  useEffect(() => {
    fetchData();
  }, [sku]);

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

  const filteredBranches = branches.filter(b =>
    !search ||
    b.branch_name_th.toLowerCase().includes(search.toLowerCase()) ||
    b.branch_name_en.toLowerCase().includes(search.toLowerCase())
  );

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
                <p className="text-sm text-gray-500">TWD Price</p>
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

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="w-[50px] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">No.</th>
                  <th className="w-[120px] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Retailer</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Branch (TH)</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Branch (EN)</th>
                  <th className="w-[120px] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Code</th>
                  <th className="w-[120px] px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Price</th>
                  <th className="w-[160px] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="w-[140px] px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Updated</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {/* TWD base price row */}
                <tr className="bg-cyan-50">
                  <td className="px-4 py-3 text-sm text-gray-400">—</td>
                  <td className="px-4 py-3 text-sm font-medium text-cyan-700">Thai Watsadu</td>
                  <td className="px-4 py-3 text-sm font-medium text-cyan-700 flex items-center gap-2">
                    <MapPin className="w-4 h-4" />
                    เทพารักษ์
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">Thepharak</td>
                  <td className="px-4 py-3 text-sm text-gray-400"></td>
                  <td className="px-4 py-3 text-sm font-semibold text-cyan-700 text-right">{formatPrice(product.twd_price)}</td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-1 rounded-full text-xs font-medium bg-cyan-100 text-cyan-700">My Price</span>
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-400">
                    {product.twd_updated_at
                      ? new Date(product.twd_updated_at).toLocaleDateString('th-TH', { day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit' })
                      : '—'}
                  </td>
                </tr>

                {filteredBranches.map((branch) => (
                  <tr key={branch.location_id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 text-sm text-gray-500 text-center">{branch.no}</td>
                    <td className="px-4 py-3 text-sm text-gray-900">Global House</td>
                    <td className="px-4 py-3 text-sm text-gray-900 flex items-center gap-2">
                      <MapPin className="w-4 h-4 text-gray-400 shrink-0" />
                      {branch.branch_name_th}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">{branch.branch_name_en}</td>
                    <td className="px-4 py-3 text-sm text-gray-500">{branch.branch_code || '—'}</td>
                    <td className={`px-4 py-3 text-sm font-semibold text-right ${
                      branch.status === 'cheaper' ? 'text-green-600' :
                      branch.status === 'higher' ? 'text-red-600' :
                      'text-gray-900'
                    }`}>
                      {formatPrice(branch.price)}
                    </td>
                    <td className="px-4 py-3">
                      {getStatusBadge(branch.status, branch.price, product.twd_price)}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-400">
                      {branch.scraped_at
                        ? new Date(branch.scraped_at).toLocaleDateString('th-TH', { day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit' })
                        : '—'}
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
