'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { MainLayout } from '@/components/layout/MainLayout';
import { Settings, MapPin, Search } from 'lucide-react';
import { apiFetch } from '@/lib/api';

interface LocationPrice {
  location_id: number;
  name: string;
  postal_code: string;
  price: number | null;
}

interface Product {
  cfw_id: number;
  cfw_sku: string;
  cfw_name: string;
  brand: string | null;
  cfw_price: number | null;
  image_url: string | null;
  category_name: string | null;
  makro_id: number;
  makro_name: string;
  watchlist_name: string;
  location_prices: LocationPrice[];
}

interface Watchlist {
  id: number;
  name: string;
}

const fmt = (p: number | null) =>
  p == null ? '—' : `฿${p.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

export default function PriceByLocationMakroPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [watchlistId, setWatchlistId] = useState<number | null>(null);
  const [page, setPage] = useState(1);
  const pageSize = 50;

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams({ page: page.toString(), page_size: pageSize.toString() });
      if (search) params.set('search', search);
      if (watchlistId) params.set('watchlist_id', watchlistId.toString());
      const res = await apiFetch(`/api/pbl/products?${params}`);
      if (res.ok) {
        const data = await res.json();
        setProducts(data.products);
        setWatchlists(data.watchlists);
        setTotal(data.total);
      }
    } finally {
      setIsLoading(false);
    }
  }, [page, search, watchlistId]);

  useEffect(() => {
    const t = setTimeout(fetchData, search ? 300 : 0);
    return () => clearTimeout(t);
  }, [fetchData]);

  const totalPages = Math.ceil(total / pageSize);

  const getMinCompetitor = (lps: LocationPrice[]) => {
    const withPrice = lps.filter((l): l is LocationPrice & { price: number } => l.price !== null);
    if (withPrice.length === 0) return null;
    return withPrice.reduce((a, b) => b.price < a.price ? b : a);
  };

  const getBranchCount = (lps: LocationPrice[]) =>
    lps.filter(l => l.price !== null).length;

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Price by Location</h1>
            <p className="text-gray-500 mt-1">Makro branch prices vs CFW for monitored watchlists</p>
          </div>
          <Link
            href="/price-by-location-makro/settings"
            className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50 transition-colors"
          >
            <Settings className="w-4 h-4" />
            Settings
          </Link>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-4 flex items-center gap-3">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search by name or SKU..."
              value={search}
              onChange={e => { setSearch(e.target.value); setPage(1); }}
              className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-cyan-400"
            />
          </div>
          {watchlists.length > 1 && (
            <select
              value={watchlistId ?? ''}
              onChange={e => { setWatchlistId(e.target.value ? Number(e.target.value) : null); setPage(1); }}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-cyan-400"
            >
              <option value="">All Watchlists</option>
              {watchlists.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}
            </select>
          )}
          <span className="text-sm text-gray-500 ml-auto">{total} products</span>
        </div>

        {/* Table */}
        {isLoading ? (
          <div className="flex justify-center py-20">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-500" />
          </div>
        ) : products.length === 0 ? (
          <div className="text-center py-20 bg-white rounded-xl shadow text-gray-400">
            <MapPin className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p className="font-medium">No products found</p>
            <p className="text-sm mt-1">
              {watchlists.length === 0
                ? 'Configure watchlists and locations in Settings first'
                : 'No verified Makro matches found for monitored watchlists'}
            </p>
          </div>
        ) : (
          <div className="bg-white rounded-xl shadow overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50 text-xs text-gray-500 uppercase">
                  <th className="px-4 py-3 text-left">SKU</th>
                  <th className="px-4 py-3 text-left">Product Name</th>
                  <th className="px-4 py-3 text-center">Buyer ID</th>
                  <th className="px-4 py-3 text-right">My Min Price</th>
                  <th className="px-4 py-3 text-right">Competitor Min Price</th>
                  <th className="px-4 py-3 text-center">Branches</th>
                </tr>
              </thead>
              <tbody>
                {products.map(p => {
                  const minCompetitor = getMinCompetitor(p.location_prices);
                  const branchCount = getBranchCount(p.location_prices);
                  return (
                    <tr
                      key={p.cfw_id}
                      className="border-b border-gray-100 hover:bg-cyan-50 transition-colors cursor-pointer"
                      onClick={() => window.location.href = `/price-by-location-makro/${p.cfw_sku}`}
                    >
                      <td className="px-4 py-3 font-mono text-gray-600 text-xs">{p.cfw_sku}</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          {p.image_url && (
                            <img src={p.image_url} alt="" className="w-8 h-8 object-contain rounded flex-shrink-0" referrerPolicy="no-referrer" />
                          )}
                          <div>
                            <div className="font-medium text-gray-900 line-clamp-1">{p.cfw_name}</div>
                            {p.brand && <div className="text-xs text-gray-400">{p.brand}</div>}
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className="text-xs font-mono bg-gray-100 text-gray-600 px-2 py-0.5 rounded">DF8</span>
                      </td>
                      <td className="px-4 py-3 text-right whitespace-nowrap">
                        <div className="font-medium text-gray-900">{fmt(p.cfw_price)}</div>
                        <div className="text-xs text-gray-400 mt-0.5">All branches</div>
                      </td>
                      <td className="px-4 py-3 text-right whitespace-nowrap">
                        {minCompetitor ? (
                          <>
                            <div className={`font-medium ${minCompetitor.price < (p.cfw_price ?? Infinity) ? 'text-red-600' : 'text-green-600'}`}>
                              {fmt(minCompetitor.price)}
                            </div>
                            <div className="text-xs text-gray-400 mt-0.5 truncate max-w-[140px] ml-auto">{minCompetitor.name}</div>
                          </>
                        ) : (
                          <span className="text-gray-400">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className="text-xs bg-blue-100 text-blue-700 font-semibold px-2 py-0.5 rounded-full">
                          {branchCount}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between text-sm text-gray-600">
            <span>{total} products total</span>
            <div className="flex gap-2">
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
                className="px-3 py-1.5 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-40">
                Previous
              </button>
              <span className="px-3 py-1.5">Page {page} of {totalPages}</span>
              <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}
                className="px-3 py-1.5 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-40">
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  );
}
