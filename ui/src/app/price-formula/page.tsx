'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Search, Save, X, Check } from 'lucide-react';
import { apiFetch } from '@/lib/api';

interface Match {
  match_id: number;
  price_formula: string | null;
  cfw_sku: string;
  cfw_name: string;
  cfw_brand: string | null;
  cfw_price: number | null;
  cfw_image: string | null;
  makro_sku: string;
  makro_name: string;
  makro_price: number | null;
  makro_image: string | null;
}

function applyFormula(makroPrice: number | null, formula: string | null): number | null {
  if (!makroPrice || !formula) return makroPrice;
  try {
    // Accepted formats: *5, /2, *5/2, /3*2
    const cleaned = formula.trim();
    let result = makroPrice;
    const parts = cleaned.match(/([*/][0-9]+(?:\.[0-9]+)?)/g);
    if (!parts) return null;
    for (const part of parts) {
      const op = part[0];
      const num = parseFloat(part.slice(1));
      if (!num) return null;
      if (op === '*') result = result * num;
      else if (op === '/') result = result / num;
    }
    return result;
  } catch {
    return null;
  }
}

function FormulaRow({ match, onSaved }: { match: Match; onSaved: (matchId: number, formula: string | null) => void }) {
  const [formula, setFormula] = useState(match.price_formula ?? '');
  const [saving, setSaving] = useState(false);
  const [savedOk, setSavedOk] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isDirty = formula !== (match.price_formula ?? '');
  const adjusted = applyFormula(match.makro_price, formula || null);

  const diff = (cfw: number | null, adj: number | null) => {
    if (!cfw || !adj) return null;
    return ((adj - cfw) / cfw) * 100;
  };

  const formatPrice = (p: number | null) => p == null ? '—' : `฿${p.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      const res = await apiFetch(`/api/price-formula/${match.match_id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ price_formula: formula.trim() || null }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || 'Failed to save');
        return;
      }
      onSaved(match.match_id, data.price_formula);
      setSavedOk(true);
      setTimeout(() => setSavedOk(false), 2000);
    } finally {
      setSaving(false);
    }
  };

  const d = diff(match.cfw_price, adjusted);

  return (
    <tr className="hover:bg-gray-50 transition-colors border-b border-gray-100">
      {/* CFW */}
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          {match.cfw_image && (
            <img src={match.cfw_image} alt="" className="w-9 h-9 object-contain rounded flex-shrink-0" referrerPolicy="no-referrer" />
          )}
          <div>
            <div className="text-sm font-medium text-gray-900 line-clamp-1">{match.cfw_name}</div>
            <div className="text-xs text-gray-400">{match.cfw_sku}{match.cfw_brand ? ` · ${match.cfw_brand}` : ''}</div>
          </div>
        </div>
      </td>
      <td className="px-4 py-3 text-right font-medium text-gray-900 text-sm whitespace-nowrap">
        {formatPrice(match.cfw_price)}
      </td>

      {/* Formula input */}
      <td className="px-4 py-3">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={formula}
              onChange={e => { setFormula(e.target.value); setError(null); }}
              onKeyDown={e => e.key === 'Enter' && isDirty && handleSave()}
              placeholder="e.g. /5  *2  /5*2"
              className={`w-32 px-2 py-1.5 border rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-cyan-400 ${
                error ? 'border-red-400' : 'border-gray-300'
              }`}
            />
            {isDirty && (
              <button
                onClick={handleSave}
                disabled={saving}
                className="p-1.5 bg-cyan-500 hover:bg-cyan-600 text-white rounded-lg transition-colors disabled:opacity-50"
                title="Save"
              >
                {saving ? (
                  <div className="w-4 h-4 border-2 border-white/50 border-t-white rounded-full animate-spin" />
                ) : (
                  <Save className="w-4 h-4" />
                )}
              </button>
            )}
            {!isDirty && savedOk && (
              <Check className="w-4 h-4 text-emerald-500" />
            )}
            {!isDirty && match.price_formula && !savedOk && (
              <button
                onClick={() => { setFormula(''); }}
                className="p-1 text-gray-300 hover:text-red-400 transition-colors"
                title="Clear formula"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
          {error && <p className="text-xs text-red-500">{error}</p>}
        </div>
      </td>

      {/* Adjusted Makro price */}
      <td className="px-4 py-3 text-right text-sm whitespace-nowrap">
        {formula && adjusted != null ? (
          <span className="font-medium text-cyan-700">{formatPrice(adjusted)}</span>
        ) : (
          <span className="text-gray-400 text-xs">—</span>
        )}
      </td>

      {/* Makro */}
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          {match.makro_image && (
            <img src={match.makro_image} alt="" className="w-9 h-9 object-contain rounded flex-shrink-0" referrerPolicy="no-referrer" />
          )}
          <div>
            <div className="text-sm font-medium text-gray-900 line-clamp-1">{match.makro_name}</div>
            <div className="text-xs text-gray-400">{match.makro_sku}</div>
          </div>
        </div>
      </td>
      <td className="px-4 py-3 text-right font-medium text-gray-900 text-sm whitespace-nowrap">
        {formatPrice(match.makro_price)}
      </td>

      {/* Diff */}
      <td className="px-4 py-3 text-center">
        {d != null ? (
          <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
            d > 0 ? 'bg-red-100 text-red-700' :
            d < 0 ? 'bg-green-100 text-green-700' :
            'bg-gray-100 text-gray-600'
          }`}>
            {d > 0 ? '+' : ''}{d.toFixed(1)}%
          </span>
        ) : '—'}
      </td>
    </tr>
  );
}

export default function PriceFormulaPage() {
  const [matches, setMatches] = useState<Match[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 50;

  const fetchMatches = useCallback(async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams({ page: page.toString(), page_size: pageSize.toString() });
      if (search) params.set('search', search);
      const res = await apiFetch(`/api/price-formula?${params}`);
      if (res.ok) {
        const data = await res.json();
        setMatches(data.matches);
        setTotal(data.total);
      }
    } finally {
      setIsLoading(false);
    }
  }, [page, search]);

  useEffect(() => {
    const timer = setTimeout(fetchMatches, search ? 300 : 0);
    return () => clearTimeout(timer);
  }, [fetchMatches]);

  const handleSaved = (matchId: number, formula: string | null) => {
    setMatches(prev => prev.map(m => m.match_id === matchId ? { ...m, price_formula: formula } : m));
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Price Formula</h1>
          <p className="text-gray-500 mt-1">
            Adjust Makro prices to match CFW unit size for fair comparison
          </p>
        </div>

        {/* Info box */}
        <div className="bg-cyan-50 border border-cyan-200 rounded-lg px-4 py-3 text-sm text-cyan-800">
          <strong>How to use:</strong> Enter a formula to adjust the Makro price to the same unit as CFW.
          Use <code className="bg-cyan-100 px-1 rounded">/5</code> to divide by 5,{' '}
          <code className="bg-cyan-100 px-1 rounded">*2</code> to multiply by 2,{' '}
          <code className="bg-cyan-100 px-1 rounded">/5*2</code> to chain operations.
          Press Enter or click Save to apply.
        </div>

        {/* Search */}
        <div className="bg-white rounded-lg shadow p-4">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Search by CFW or Makro name / SKU..."
              value={search}
              onChange={e => { setSearch(e.target.value); setPage(1); }}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* Table */}
        <div className="bg-white rounded-xl shadow overflow-hidden">
          {isLoading ? (
            <div className="flex justify-center py-20">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-500" />
            </div>
          ) : matches.length === 0 ? (
            <div className="text-center py-20 text-gray-400">
              <p className="font-medium">No verified matches found</p>
              <p className="text-sm mt-1">Verify matches on the product detail page first</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50 text-xs text-gray-500 uppercase">
                    <th className="px-4 py-3 text-left">CFW Product</th>
                    <th className="px-4 py-3 text-right">CFW Price</th>
                    <th className="px-4 py-3 text-left">Formula (Makro)</th>
                    <th className="px-4 py-3 text-right">Adjusted Makro</th>
                    <th className="px-4 py-3 text-left">Makro Product</th>
                    <th className="px-4 py-3 text-right">Makro Price</th>
                    <th className="px-4 py-3 text-center">Diff</th>
                  </tr>
                </thead>
                <tbody>
                  {matches.map(m => (
                    <FormulaRow key={m.match_id} match={m} onSaved={handleSaved} />
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between text-sm text-gray-600">
            <span>{total} matches total</span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1.5 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-40"
              >
                Previous
              </button>
              <span className="px-3 py-1.5">Page {page} of {totalPages}</span>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-3 py-1.5 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  );
}
