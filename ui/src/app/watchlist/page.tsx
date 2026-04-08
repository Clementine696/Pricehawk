'use client';

import React, { useState, useEffect } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Plus, Trash2, Search, Package, X, CheckCircle, FolderOpen, Download } from 'lucide-react';
import { apiFetch } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { MultiSelect } from '@/components/ui/MultiSelect';

interface Watchlist {
  id: number;
  name: string;
  description: string | null;
  product_count: number;
  created_at: string;
}

interface WatchlistProduct {
  id: number;
  sku: string;
  name: string;
  brand: string | null;
  current_price: number | null;
  image_url: string | null;
  url: string | null;
  category_name: string | null;
  makro_price: number | null;
  makro_name: string | null;
  added_at: string;
}

interface AvailableProduct {
  id: number;
  sku: string;
  name: string;
  brand: string | null;
  current_price: number | null;
  image_url: string | null;
  category_name: string | null;
}

export default function WatchlistPage() {
  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Manage products modal
  const [selectedWatchlist, setSelectedWatchlist] = useState<Watchlist | null>(null);
  const [watchlistProducts, setWatchlistProducts] = useState<WatchlistProduct[]>([]);
  const [loadingProducts, setLoadingProducts] = useState(false);

  // Available products search
  const [availableProducts, setAvailableProducts] = useState<AvailableProduct[]>([]);
  const [loadingAvailable, setLoadingAvailable] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedBrands, setSelectedBrands] = useState<string[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [allBrands, setAllBrands] = useState<string[]>([]);
  const [allCategories, setAllCategories] = useState<string[]>([]);

  // Create modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  // Export
  const [exportingId, setExportingId] = useState<number | null>(null);

  // Delete
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [removingProduct, setRemovingProduct] = useState<number | null>(null);
  const [addingProduct, setAddingProduct] = useState<string | null>(null);

  useEffect(() => {
    fetchWatchlists();
  }, []);

  useEffect(() => {
    if (selectedWatchlist) {
      fetchAvailableProducts();
    }
  }, [selectedWatchlist, searchTerm, selectedBrands, selectedCategories]);

  const fetchWatchlists = async () => {
    setIsLoading(true);
    try {
      const res = await apiFetch('/api/watchlists');
      if (res.ok) {
        const data = await res.json();
        setWatchlists(data.watchlists);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const fetchWatchlistProducts = async (watchlistId: number) => {
    setLoadingProducts(true);
    try {
      const res = await apiFetch(`/api/watchlists/${watchlistId}/products`);
      if (res.ok) {
        const data = await res.json();
        setWatchlistProducts(data.products);
      }
    } finally {
      setLoadingProducts(false);
    }
  };

  const fetchAvailableProducts = async () => {
    setLoadingAvailable(true);
    try {
      const params = new URLSearchParams({ search: searchTerm, page_size: '500' });
      if (selectedBrands.length > 0) params.set('brand', selectedBrands.join(','));
      const res = await apiFetch(`/api/products?${params}`);
      if (res.ok) {
        const data = await res.json();
        const products: AvailableProduct[] = data.products || [];
        setAvailableProducts(products);
        // Build filter options from unfiltered load
        if (selectedBrands.length === 0 && !searchTerm) {
          setAllBrands(Array.from(new Set(products.map(p => p.brand).filter(Boolean) as string[])).sort());
          setAllCategories(Array.from(new Set(products.map(p => p.category_name).filter(Boolean) as string[])).sort());
        }
      }
    } finally {
      setLoadingAvailable(false);
    }
  };

  const handleExport = async (w: Watchlist) => {
    setExportingId(w.id);
    try {
      const res = await apiFetch(`/api/watchlists/${w.id}/export`);
      if (!res.ok) throw new Error('Export failed');
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      const now = new Date();
      const ts = now.getFullYear().toString() +
        (now.getMonth() + 1).toString().padStart(2, '0') +
        now.getDate().toString().padStart(2, '0') + '_' +
        now.getHours().toString().padStart(2, '0') +
        now.getMinutes().toString().padStart(2, '0');
      link.download = `${w.name.replace(/\s+/g, '_')}_${ts}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (e) {
      console.error('Export failed', e);
    } finally {
      setExportingId(null);
    }
  };

  const openManageModal = async (watchlist: Watchlist) => {
    setSelectedWatchlist(watchlist);
    setSearchTerm('');
    setWatchlistProducts([]);
    await fetchWatchlistProducts(watchlist.id);
  };

  const closeManageModal = () => {
    setSelectedWatchlist(null);
    setWatchlistProducts([]);
    setAvailableProducts([]);
    setSearchTerm('');
    setSelectedBrands([]);
    setSelectedCategories([]);
    setAllBrands([]);
    setAllCategories([]);
  };

  const handleCreate = async () => {
    if (!newName.trim()) { setCreateError('Name is required'); return; }
    setIsCreating(true);
    setCreateError(null);
    try {
      const res = await apiFetch('/api/watchlists', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newName.trim(), description: newDesc.trim() || null }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setCreateError(err.detail || 'Failed to create watchlist');
        return;
      }
      const created = await res.json();
      setWatchlists(prev => [{ ...created, product_count: 0 }, ...prev]);
      setNewName('');
      setNewDesc('');
      setShowCreateModal(false);
    } finally {
      setIsCreating(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this watchlist and all its products?')) return;
    setDeletingId(id);
    try {
      const res = await apiFetch(`/api/watchlists/${id}`, { method: 'DELETE' });
      if (res.ok) {
        setWatchlists(prev => prev.filter(w => w.id !== id));
      }
    } finally {
      setDeletingId(null);
    }
  };

  const handleAddProduct = async (productId: number, sku: string) => {
    if (!selectedWatchlist) return;
    setAddingProduct(sku);
    try {
      const res = await apiFetch(`/api/watchlists/${selectedWatchlist.id}/products`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sku }),
      });
      if (res.ok) {
        await fetchWatchlistProducts(selectedWatchlist.id);
        setWatchlists(prev => prev.map(w =>
          w.id === selectedWatchlist.id ? { ...w, product_count: w.product_count + 1 } : w
        ));
        setSelectedWatchlist(prev => prev ? { ...prev, product_count: prev.product_count + 1 } : prev);
      }
    } finally {
      setAddingProduct(null);
    }
  };

  const handleRemoveProduct = async (productId: number) => {
    if (!selectedWatchlist) return;
    setRemovingProduct(productId);
    try {
      const res = await apiFetch(`/api/watchlists/${selectedWatchlist.id}/products/${productId}`, { method: 'DELETE' });
      if (res.ok) {
        setWatchlistProducts(prev => prev.filter(p => p.id !== productId));
        setWatchlists(prev => prev.map(w =>
          w.id === selectedWatchlist.id ? { ...w, product_count: Math.max(0, w.product_count - 1) } : w
        ));
        setSelectedWatchlist(prev => prev ? { ...prev, product_count: Math.max(0, prev.product_count - 1) } : prev);
      }
    } finally {
      setRemovingProduct(null);
    }
  };

  const addedSkus = new Set(watchlistProducts.map(p => p.sku));
  const filteredAvailable = availableProducts.filter(p => {
    if (addedSkus.has(p.sku)) return false;
    if (selectedCategories.length > 0 && !selectedCategories.includes(p.category_name ?? '')) return false;
    return true;
  });

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Watchlist</h1>
            <p className="text-gray-500 mt-1">Track specific products and compare CFW vs Makro prices</p>
          </div>
          <Button variant="primary" icon={<Plus className="w-4 h-4" />} onClick={() => setShowCreateModal(true)}>
            New Watchlist
          </Button>
        </div>

        {/* Loading */}
        {isLoading && (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-500" />
          </div>
        )}

        {/* Empty */}
        {!isLoading && watchlists.length === 0 && (
          <div className="text-center py-20 bg-white rounded-lg shadow">
            <FolderOpen className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p className="font-medium text-gray-900 text-lg">No watchlists yet</p>
            <p className="text-sm mt-1 text-gray-500">Create one to start tracking products</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700"
            >
              <Plus className="w-5 h-5" />
              New Watchlist
            </button>
          </div>
        )}

        {/* Watchlist cards */}
        {!isLoading && watchlists.length > 0 && (
          <div className="space-y-4">
            {watchlists.map(w => (
              <div key={w.id} className="bg-white rounded-lg shadow hover:shadow-md transition-shadow">
                <div className="p-6 flex items-center justify-between gap-6">
                  <div className="flex-1">
                    <h2 className="text-xl font-semibold text-gray-900 mb-1">{w.name}</h2>
                    {w.description && <p className="text-sm text-gray-500 mb-2">{w.description}</p>}
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <Package className="w-4 h-4" />
                      <span>{w.product_count} product{w.product_count !== 1 ? 's' : ''}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline-success"
                      onClick={() => handleExport(w)}
                      disabled={exportingId === w.id || w.product_count === 0}
                      loading={exportingId === w.id}
                      icon={<Download className="w-4 h-4" />}
                    >
                      Export
                    </Button>
                    <Button
                      variant="outline-primary"
                      onClick={() => openManageModal(w)}
                      icon={<Package className="w-4 h-4" />}
                    >
                      Manage Products
                    </Button>
                    <button
                      onClick={() => handleDelete(w.id)}
                      disabled={deletingId === w.id}
                      className="p-2 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
                      title="Delete watchlist"
                    >
                      <Trash2 className="w-5 h-5 text-red-500" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md mx-4">
            <h2 className="text-lg font-bold text-gray-900 mb-4">New Watchlist</h2>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name <span className="text-red-500">*</span></label>
                <input
                  type="text"
                  value={newName}
                  onChange={e => setNewName(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleCreate()}
                  placeholder="e.g. Milk Products"
                  autoFocus
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-400"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <input
                  type="text"
                  value={newDesc}
                  onChange={e => setNewDesc(e.target.value)}
                  placeholder="Optional"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-400"
                />
              </div>
              {createError && <p className="text-sm text-red-500">{createError}</p>}
            </div>
            <div className="flex gap-3 mt-5">
              <Button variant="outline" onClick={() => { setShowCreateModal(false); setNewName(''); setNewDesc(''); setCreateError(null); }}>
                Cancel
              </Button>
              <Button variant="primary" loading={isCreating} onClick={handleCreate}>
                Create
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Manage Products Full-Screen Modal */}
      {selectedWatchlist && (
        <div className="fixed inset-0 bg-white z-50 flex flex-col">
          {/* Header */}
          <div className="px-6 py-4 border-b border-gray-200 bg-white flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Manage Products — {selectedWatchlist.name}</h2>
              <p className="text-sm text-gray-500 mt-1">{selectedWatchlist.product_count} products in this watchlist</p>
            </div>
            <button onClick={closeManageModal} className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
              <X className="w-6 h-6 text-gray-500" />
            </button>
          </div>

          {/* Two Column Layout */}
          <div className="flex-1 flex overflow-hidden">
            {/* Left — Added Products */}
            <div className="w-1/3 border-r border-gray-200 flex flex-col">
              <div className="px-6 py-4 bg-green-50 border-b border-green-200">
                <h3 className="font-semibold text-green-900 flex items-center gap-2">
                  <CheckCircle className="w-5 h-5" />
                  Added Products
                </h3>
                <p className="text-sm text-green-700 mt-1">{watchlistProducts.length} in this watchlist</p>
              </div>
              <div className="flex-1 overflow-y-auto">
                {loadingProducts ? (
                  <div className="flex justify-center py-12">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-cyan-500" />
                  </div>
                ) : watchlistProducts.length === 0 ? (
                  <p className="text-gray-500 text-center py-8 text-sm">No products added yet</p>
                ) : (
                  <div className="divide-y divide-gray-100">
                    {watchlistProducts.map(p => (
                      <div key={p.id} className="flex items-center gap-2 px-4 py-2.5 hover:bg-gray-50 transition-colors">
                        {p.image_url && (
                          <img src={p.image_url} alt="" className="w-8 h-8 object-contain rounded flex-shrink-0" referrerPolicy="no-referrer" />
                        )}
                        <div className="text-xs font-mono text-gray-500 w-20 flex-shrink-0">{p.sku}</div>
                        <div className="text-sm text-gray-800 w-16 flex-shrink-0">
                          {p.current_price ? `฿${p.current_price.toLocaleString()}` : '—'}
                        </div>
                        <div className="flex-1 min-w-0 text-sm text-gray-900 truncate">{p.name}</div>
                        <button
                          onClick={() => handleRemoveProduct(p.id)}
                          disabled={removingProduct === p.id}
                          className="p-1 hover:bg-gray-200 rounded transition-colors flex-shrink-0 disabled:opacity-50"
                          title="Remove"
                        >
                          <Trash2 className="w-4 h-4 text-gray-500" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Right — Available Products */}
            <div className="flex-1 flex flex-col">
              <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
                <h3 className="font-semibold text-gray-900 mb-3">Available CFW Products</h3>
                <div className="grid grid-cols-12 gap-3">
                  <div className="col-span-6 relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
                    <input
                      type="text"
                      placeholder="Search by name or SKU..."
                      value={searchTerm}
                      onChange={e => setSearchTerm(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
                    />
                  </div>
                  <div className="col-span-3">
                    <MultiSelect
                      options={allBrands}
                      selected={selectedBrands}
                      onChange={setSelectedBrands}
                      placeholder="All Brands"
                    />
                  </div>
                  <div className="col-span-3">
                    <MultiSelect
                      options={allCategories}
                      selected={selectedCategories}
                      onChange={setSelectedCategories}
                      placeholder="All Categories"
                    />
                  </div>
                </div>
              </div>
              <div className="flex-1 overflow-y-auto">
                {loadingAvailable ? (
                  <div className="flex justify-center py-12">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-cyan-500" />
                  </div>
                ) : filteredAvailable.length === 0 ? (
                  <p className="text-gray-500 text-center py-8 text-sm">No products found</p>
                ) : (
                  <div className="divide-y divide-gray-100">
                    {filteredAvailable.map(p => (
                      <button
                        key={p.sku}
                        onClick={() => handleAddProduct(p.id, p.sku)}
                        disabled={addingProduct === p.sku}
                        className="w-full text-left flex items-center gap-2 px-4 py-2.5 hover:bg-cyan-50 transition-colors disabled:opacity-50"
                      >
                        {p.image_url && (
                          <img src={p.image_url} alt="" className="w-8 h-8 object-contain rounded flex-shrink-0" referrerPolicy="no-referrer" />
                        )}
                        <div className="text-xs font-mono text-gray-500 w-20 flex-shrink-0">{p.sku}</div>
                        <div className="text-sm text-gray-800 w-16 flex-shrink-0">
                          {p.current_price ? `฿${p.current_price.toLocaleString()}` : '—'}
                        </div>
                        <div className="flex-1 min-w-0 text-sm text-gray-900 truncate">{p.name}</div>
                        <Plus className="w-4 h-4 text-gray-400 flex-shrink-0" />
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </MainLayout>
  );
}
