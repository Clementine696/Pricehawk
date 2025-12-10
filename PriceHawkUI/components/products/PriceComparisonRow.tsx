import React from 'react';
import { ProductComparison, Retailer, ValidationStatus } from '@/lib/types/price-comparison';
import { PriceCell } from './PriceCell';
import { StatusBadge } from './StatusBadge';
import { getPriceComparisonCategory } from '@/lib/utils/price-utils';
import { isManualProductId } from '@/lib/utils/manual-comparison-storage';

interface PriceComparisonRowProps {
  product: ProductComparison;
  rowNumber: number;
  onRowClick?: (product: ProductComparison) => void;
  validationStatuses?: Record<string, Record<string, ValidationStatus>>;
}

export const PriceComparisonRow: React.FC<PriceComparisonRowProps> = ({
  product,
  rowNumber,
  onRowClick,
  validationStatuses,
}) => {
  const handleClick = () => {
    if (onRowClick) {
      onRowClick(product);
    }
  };

  // Extract all valid prices for comparison
  const allValidPrices = Object.values(product.prices)
    .map((p) => p.price)
    .filter((p): p is number => p !== null && p > 0);

  // Helper function to check if a retailer's matched product is marked as incorrect
  const isRetailerPriceHidden = (retailer: Retailer): boolean => {
    if (!validationStatuses || !validationStatuses[product.id]) {
      return false;
    }
    const matchedProductId = `${retailer.toLowerCase()}_${product.sku}`;
    return validationStatuses[product.id][matchedProductId] === 'incorrect';
  };

  // Check if this is a manual entry
  const isManual = isManualProductId(product.id);

  return (
    <tr
      className="border-b hover:bg-gray-50 cursor-pointer transition-colors"
      onClick={handleClick}
    >
      {/* 1. NO. */}
      <td className="px-4 py-3 text-sm text-gray-700 text-center">{rowNumber}</td>

      {/* 2. SKU */}
      <td className="px-4 py-3 text-sm font-mono text-gray-700">
        <div className="flex items-center gap-2">
          {product.sku}
          {isManual && (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
              Manual
            </span>
          )}
        </div>
      </td>

      {/* 3. PRODUCT NAME */}
      <td className="px-4 py-3 text-sm text-gray-900 max-w-xs truncate" title={product.name}>
        {product.nameTh || product.name}
      </td>

      {/* 4. BRAND */}
      <td className="px-4 py-3 text-sm text-gray-700">{product.brand}</td>

      {/* 5. CATEGORY */}
      <td className="px-4 py-3 text-sm text-gray-700">
        {product.categoryTh || product.category}
      </td>

      {/* 6. STATUS */}
      <td className="px-4 py-3 text-sm">
        <StatusBadge status={product.status} />
      </td>

      {/* 7. THAI WATSADU price */}
      <td className="px-4 py-3 text-sm">
        <PriceCell
          price={product.prices[Retailer.THAI_WATSADU].price}
          productUrl={product.prices[Retailer.THAI_WATSADU].productUrl}
          comparisonCategory={getPriceComparisonCategory(
            product.prices[Retailer.THAI_WATSADU].price,
            allValidPrices
          )}
        />
      </td>

      {/* 8. HOMEPRO price */}
      <td className="px-4 py-3 text-sm">
        <PriceCell
          price={product.prices[Retailer.HOMEPRO].price}
          productUrl={product.prices[Retailer.HOMEPRO].productUrl}
          comparisonCategory={getPriceComparisonCategory(
            product.prices[Retailer.HOMEPRO].price,
            allValidPrices
          )}
          hidden={isRetailerPriceHidden(Retailer.HOMEPRO)}
        />
      </td>

      {/* 9. GLOBAL HOUSE price */}
      <td className="px-4 py-3 text-sm">
        <PriceCell
          price={product.prices[Retailer.GLOBAL_HOUSE].price}
          productUrl={product.prices[Retailer.GLOBAL_HOUSE].productUrl}
          comparisonCategory={getPriceComparisonCategory(
            product.prices[Retailer.GLOBAL_HOUSE].price,
            allValidPrices
          )}
          hidden={isRetailerPriceHidden(Retailer.GLOBAL_HOUSE)}
        />
      </td>

      {/* 10. DO HOME price */}
      <td className="px-4 py-3 text-sm">
        <PriceCell
          price={product.prices[Retailer.DOHOME].price}
          productUrl={product.prices[Retailer.DOHOME].productUrl}
          comparisonCategory={getPriceComparisonCategory(
            product.prices[Retailer.DOHOME].price,
            allValidPrices
          )}
          hidden={isRetailerPriceHidden(Retailer.DOHOME)}
        />
      </td>

      {/* 11. BOONTHAVORN price */}
      <td className="px-4 py-3 text-sm">
        <PriceCell
          price={product.prices[Retailer.BOONTHAVORN].price}
          productUrl={product.prices[Retailer.BOONTHAVORN].productUrl}
          comparisonCategory={getPriceComparisonCategory(
            product.prices[Retailer.BOONTHAVORN].price,
            allValidPrices
          )}
          hidden={isRetailerPriceHidden(Retailer.BOONTHAVORN)}
        />
      </td>
    </tr>
  );
};
