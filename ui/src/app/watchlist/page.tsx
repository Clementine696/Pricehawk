'use client';

import React, { useState, useEffect } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Eye, EyeOff, Search, Package, Download, Loader2 } from 'lucide-react';
import { apiFetch } from '@/lib/api';

interface CategoryItem {
  category: string;
  product_count: number;
  is_watched: boolean;
}

export default function WatchlistPage() {
  const [categories, setCategories] = useState<CategoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [updating, setUpdating] = useState<string | null>(null);
  const [isExporting, setIsExporting] = useState(false);

  useEffect(() => {
    fetchCategories();
  }, []);

  const fetchCategories = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiFetch('/api/watchlist/categories');
      if (!response.ok) {
        throw new Error('Failed to fetch categories');
      }
      const data = await response.json();
      setCategories(data.categories);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleWatch = async (category: string, currentlyWatched: boolean) => {
    setUpdating(category);
    try {
      if (currentlyWatched) {
        // Remove from watchlist
        const response = await apiFetch(`/api/watchlist/${encodeURIComponent(category)}`, {
          method: 'DELETE',
        });
        if (!response.ok) throw new Error('Failed to remove from watchlist');
      } else {
        // Add to watchlist
        const response = await apiFetch('/api/watchlist', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ category }),
        });
        if (!response.ok) throw new Error('Failed to add to watchlist');
      }

      // Update local state
      setCategories(prev =>
        prev.map(c =>
          c.category === category ? { ...c, is_watched: !currentlyWatched } : c
        )
      );
    } catch (err) {
      console.error('Error toggling watch:', err);
    } finally {
      setUpdating(null);
    }
  };

  const handleExport = async () => {
    setIsExporting(true);
    try {
      const response = await apiFetch('/api/products/export?watched_only=true');
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
      link.download = `watchlist_export_${timestamp}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting watchlist:', error);
    } finally {
      setIsExporting(false);
    }
  };

  // Filter categories by search
  const filteredCategories = categories.filter(c =>
    c.category.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Separate watched and unwatched
  const watchedCategories = filteredCategories.filter(c => c.is_watched);
  const unwatchedCategories = filteredCategories.filter(c => !c.is_watched);

  if (isLoading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading categories...</p>
          </div>
        </div>
      </MainLayout>
    );
  }

  if (error) {
    return (
      <MainLayout>
        <div className="flex flex-col items-center justify-center min-h-[400px]">
          <p className="text-red-500 mb-4">{error}</p>
          <button
            onClick={fetchCategories}
            className="text-cyan-500 hover:text-cyan-600"
          >
            Try again
          </button>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Category Watchlist</h1>
            <p className="text-gray-600 mt-1">
              Select categories to watch for price changes. You are watching {watchedCategories.length} of {categories.length} categories.
            </p>
          </div>
          {watchedCategories.length > 0 && (
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
                  Export Watchlist
                </>
              )}
            </button>
          )}
        </div>

        {/* Search */}
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search categories..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-400"
          />
        </div>

        {/* Watched Categories */}
        {watchedCategories.length > 0 && (
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <Eye className="w-5 h-5 text-cyan-500" />
              Watching ({watchedCategories.length})
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {watchedCategories.map((item) => (
                <div
                  key={item.category}
                  className="bg-cyan-50 border border-cyan-200 rounded-lg p-4 flex items-center justify-between"
                >
                  <div>
                    <p className="font-medium text-gray-900">{item.category}</p>
                    <p className="text-sm text-gray-500 flex items-center gap-1">
                      <Package className="w-4 h-4" />
                      {item.product_count} products
                    </p>
                  </div>
                  <button
                    onClick={() => toggleWatch(item.category, true)}
                    disabled={updating === item.category}
                    className="p-2 text-cyan-600 hover:bg-cyan-100 rounded-lg transition-colors disabled:opacity-50"
                    title="Stop watching"
                  >
                    {updating === item.category ? (
                      <div className="w-5 h-5 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <Eye className="w-5 h-5" />
                    )}
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Unwatched Categories */}
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <EyeOff className="w-5 h-5 text-gray-400" />
            Not Watching ({unwatchedCategories.length})
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {unwatchedCategories.map((item) => (
              <div
                key={item.category}
                className="bg-white border border-gray-200 rounded-lg p-4 flex items-center justify-between hover:border-gray-300 transition-colors"
              >
                <div>
                  <p className="font-medium text-gray-900">{item.category}</p>
                  <p className="text-sm text-gray-500 flex items-center gap-1">
                    <Package className="w-4 h-4" />
                    {item.product_count} products
                  </p>
                </div>
                <button
                  onClick={() => toggleWatch(item.category, false)}
                  disabled={updating === item.category}
                  className="p-2 text-gray-400 hover:text-cyan-500 hover:bg-cyan-50 rounded-lg transition-colors disabled:opacity-50"
                  title="Start watching"
                >
                  {updating === item.category ? (
                    <div className="w-5 h-5 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <EyeOff className="w-5 h-5" />
                  )}
                </button>
              </div>
            ))}
          </div>
        </div>

        {filteredCategories.length === 0 && searchQuery && (
          <div className="text-center py-8 text-gray-500">
            No categories found matching "{searchQuery}"
          </div>
        )}
      </div>
    </MainLayout>
  );
}
