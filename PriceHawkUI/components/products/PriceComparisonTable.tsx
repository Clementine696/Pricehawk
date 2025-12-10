import React from 'react';
import { ProductComparison, ValidationStatus } from '@/lib/types/price-comparison';
import { PriceComparisonRow } from './PriceComparisonRow';

interface PriceComparisonTableProps {
  products: ProductComparison[];
  isLoading?: boolean;
  onRowClick?: (product: ProductComparison) => void;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  onSort?: (column: string) => void;
  validationStatuses?: Record<string, Record<string, ValidationStatus>>;
}

export const PriceComparisonTable: React.FC<PriceComparisonTableProps> = ({
  products,
  isLoading = false,
  onRowClick,
  sortBy,
  sortOrder,
  onSort,
  validationStatuses,
}) => {
  if (isLoading) {
    return (
      <div className="overflow-hidden">
        <div className="animate-pulse p-8">
          <div className="h-8 bg-gray-200 rounded mb-4"></div>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-12 bg-gray-100 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (products.length === 0) {
    return (
      <div className="p-8 text-center">
        <p className="text-gray-500 text-lg">No products found</p>
        <p className="text-gray-400 text-sm mt-2">Try adjusting your filters</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto -mx-6">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              NO.
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              SKU
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              PRODUCT NAME
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              BRAND
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              CATEGORY
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              STATUS
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              THAI WATSADU
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              HOMEPRO
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              GLOBAL HOUSE
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              DO HOME
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              BOONTHAVORN
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {products.map((product, index) => (
            <PriceComparisonRow
              key={product.id}
              product={product}
              rowNumber={index + 1}
              onRowClick={onRowClick}
              validationStatuses={validationStatuses}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
};
