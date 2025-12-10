'use client';

import React, { useState, useEffect } from 'react';
import { Search, RotateCcw } from 'lucide-react';
import { ProductFilterState } from '@/lib/types/price-comparison';

interface ProductSearchFilterProps {
  filters: ProductFilterState;
  categories: { value: string; label: string; count?: number }[];
  brands: { value: string; label: string; count?: number }[];
  onFilterChange: (filters: Partial<ProductFilterState>) => void;
  onReset: () => void;
  onExport: () => void;
}

export const ProductSearchFilter: React.FC<ProductSearchFilterProps> = ({
  filters,
  categories,
  brands,
  onFilterChange,
  onReset,
  onExport,
}) => {
  const [searchValue, setSearchValue] = useState(filters.search);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      onFilterChange({ search: searchValue });
    }, 300);

    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchValue]);

  return (
    <div className="bg-white rounded-lg shadow p-6 mb-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Search & Filter</h2>

      <div className="flex flex-wrap items-center gap-3">
        {/* Search Input */}
        <div className="flex-1 min-w-[240px]">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Search by name, SKU, brand, or retailer..."
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-sky-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* Category Filter */}
        <div className="w-[180px]">
          <select
            value={filters.category || ''}
            onChange={(e) =>
              onFilterChange({ category: e.target.value || null })
            }
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-sky-500 focus:border-transparent"
          >
            <option value="">All Categories</option>
            {categories.map((cat) => (
              <option key={cat.value} value={cat.value}>
                {cat.label} {cat.count ? `(${cat.count})` : ''}
              </option>
            ))}
          </select>
        </div>

        {/* Brand Filter */}
        <div className="w-[180px]">
          <select
            value={filters.brand || ''}
            onChange={(e) =>
              onFilterChange({ brand: e.target.value || null })
            }
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-sky-500 focus:border-transparent"
          >
            <option value="">All Brands</option>
            {brands.map((brand) => (
              <option key={brand.value} value={brand.value}>
                {brand.label} {brand.count ? `(${brand.count})` : ''}
              </option>
            ))}
          </select>
        </div>

        {/* Reset Button */}
        <button
          onClick={onReset}
          className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-sky-500"
        >
          <RotateCcw className="w-4 h-4" />
          Reset
        </button>

        {/* Export Button */}
        <button
          onClick={onExport}
          className="inline-flex items-center gap-2 px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-cyan-500 hover:bg-cyan-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-cyan-500"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
            />
          </svg>
          Export
        </button>
      </div>
    </div>
  );
};
