'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { MainLayout } from '@/components/layout/MainLayout';
import { ArrowLeft, Loader2 } from 'lucide-react';
import { apiFetch } from '@/lib/api';

interface LocationRow {
  location_id: number;
  branch_name: string;
  postal_code: string;
  makro_price: number | null;
  scraped_at: string | null;
}

interface CfwProduct {
  id: number;
  sku: string;
  name: string;
  brand: string | null;
  current_price: number | null;
  image_url: string | null;
  category_name: string | null;
}

interface MakroProduct {
  id: number;
  sku: string;
  name: string;
  current_price: number | null;
}

const fmt = (p: number | null) =>
  p == null ? '—' : `฿${p.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

function getStatus(cfw: number | null, makro: number | null): { label: string; cls: string } {
  if (!cfw || !makro) return { label: 'No Data', cls: 'bg-gray-100 text-gray-500' };
  if (makro < cfw) return { label: 'Cheaper', cls: 'bg-red-100 text-red-700' };
  if (makro > cfw) return { label: 'More Expensive', cls: 'bg-green-100 text-green-700' };
  return { label: 'Same', cls: 'bg-gray-100 text-gray-600' };
}

export default function PblDetailPage() {
  const params = useParams();
  const sku = params.sku as string;

  const [cfw, setCfw] = useState<CfwProduct | null>(null);
  const [makro, setMakro] = useState<MakroProduct | null>(null);
  const [locations, setLocations] = useState<LocationRow[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    apiFetch(`/api/pbl/products/${sku}`)
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data) {
          setCfw(data.cfw);
          setMakro(data.makro);
          setLocations(data.locations);
        }
      })
      .finally(() => setIsLoading(false));
  }, [sku]);

  if (isLoading) {
    return (
      <MainLayout>
        <div className="flex justify-center py-32">
          <Loader2 className="w-8 h-8 animate-spin text-cyan-500" />
        </div>
      </MainLayout>
    );
  }

  if (!cfw) {
    return (
      <MainLayout>
        <div className="text-center py-32 text-gray-400">Product not found</div>
      </MainLayout>
    );
  }

  const withPrice = locations.filter(l => l.makro_price !== null);
  const minPrice = withPrice.length > 0 ? Math.min(...withPrice.map(l => l.makro_price!)) : null;
  const maxPrice = withPrice.length > 0 ? Math.max(...withPrice.map(l => l.makro_price!)) : null;

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Back */}
        <Link href="/price-by-location-makro" className="inline-flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900">
          <ArrowLeft className="w-4 h-4" />
          Back to Price by Location
        </Link>

        {/* Product header */}
        <div className="bg-white rounded-xl shadow p-6">
          <div className="flex items-start gap-4">
            {cfw.image_url && (
              <img src={cfw.image_url} alt="" className="w-20 h-20 object-contain rounded-lg border border-gray-100 flex-shrink-0" referrerPolicy="no-referrer" />
            )}
            <div className="flex-1">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">{cfw.name}</h1>
                  <div className="flex items-center gap-3 mt-1 text-sm text-gray-500">
                    <span className="font-mono">{cfw.sku}</span>
                    {cfw.brand && <span>· {cfw.brand}</span>}
                    {cfw.category_name && <span>· {cfw.category_name}</span>}
                  </div>
                </div>
                <div className="text-right flex-shrink-0">
                  <div className="text-xs text-gray-400 mb-1">Buyer ID</div>
                  <span className="font-mono bg-gray-100 text-gray-700 px-3 py-1 rounded text-sm font-semibold">DF8</span>
                </div>
              </div>

              {/* Price summary */}
              <div className="mt-4 grid grid-cols-4 gap-4">
                <div className="bg-cyan-50 rounded-lg p-3">
                  <div className="text-xs text-cyan-600 mb-1">My Price (CFW)</div>
                  <div className="text-lg font-bold text-cyan-800">{fmt(cfw.current_price)}</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="text-xs text-gray-500 mb-1">Makro Default</div>
                  <div className="text-lg font-bold text-gray-700">{fmt(makro?.current_price ?? null)}</div>
                </div>
                <div className="bg-red-50 rounded-lg p-3">
                  <div className="text-xs text-red-500 mb-1">Competitor Min</div>
                  <div className="text-lg font-bold text-red-700">{fmt(minPrice)}</div>
                </div>
                <div className="bg-orange-50 rounded-lg p-3">
                  <div className="text-xs text-orange-500 mb-1">Competitor Max</div>
                  <div className="text-lg font-bold text-orange-700">{fmt(maxPrice)}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Makro match */}
        {makro && (
          <div className="bg-white rounded-xl shadow p-4 text-sm text-gray-600">
            <span className="font-medium text-gray-900">Matched Makro product:</span>{' '}
            {makro.name} <span className="font-mono text-gray-400">({makro.sku})</span>
          </div>
        )}

        {/* Location table */}
        <div className="bg-white rounded-xl shadow overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50 text-xs text-gray-500 uppercase">
                <th className="px-4 py-3 text-left">Branch (TH)</th>
                <th className="px-4 py-3 text-center">Postal Code</th>
                <th className="px-4 py-3 text-right">My Price</th>
                <th className="px-4 py-3 text-right">Makro Price</th>
                <th className="px-4 py-3 text-right">Difference</th>
                <th className="px-4 py-3 text-center">Status</th>
                <th className="px-4 py-3 text-center">Updated At</th>
              </tr>
            </thead>
            <tbody>
              {locations.map(loc => {
                const diff = cfw.current_price && loc.makro_price != null
                  ? ((loc.makro_price - cfw.current_price) / cfw.current_price) * 100
                  : null;
                const status = getStatus(cfw.current_price, loc.makro_price);
                const isMin = loc.makro_price !== null && loc.makro_price === minPrice;

                return (
                  <tr key={loc.location_id} className={`border-b border-gray-100 ${isMin ? 'bg-red-50' : 'hover:bg-gray-50'} transition-colors`}>
                    <td className="px-4 py-3 font-medium text-gray-900">{loc.branch_name}</td>
                    <td className="px-4 py-3 text-center font-mono text-gray-500">{loc.postal_code}</td>
                    <td className="px-4 py-3 text-right text-gray-700">{fmt(cfw.current_price)}</td>
                    <td className="px-4 py-3 text-right font-medium text-gray-900">
                      {loc.makro_price != null ? (
                        <span className={isMin ? 'text-red-600 font-bold' : ''}>{fmt(loc.makro_price)}</span>
                      ) : '—'}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {diff != null ? (
                        <span className={`font-medium ${diff > 0 ? 'text-green-600' : diff < 0 ? 'text-red-600' : 'text-gray-500'}`}>
                          {diff > 0 ? '+' : ''}{diff.toFixed(1)}%
                        </span>
                      ) : '—'}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${status.cls}`}>
                        {status.label}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center text-xs text-gray-400">
                      {loc.scraped_at
                        ? new Date(loc.scraped_at).toLocaleString('th-TH', { dateStyle: 'short', timeStyle: 'short' })
                        : '—'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </MainLayout>
  );
}
