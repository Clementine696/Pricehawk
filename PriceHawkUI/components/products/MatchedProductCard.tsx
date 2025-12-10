import React from 'react';
import Image from 'next/image';
import { Retailer, RetailerNames, MatchedProduct, ValidationStatus } from '@/lib/types/price-comparison';
import { formatCurrency } from '@/lib/utils/price-utils';
import { MatchTypeBadge } from './MatchTypeBadge';
import { ConfidenceBadge } from './ConfidenceBadge';
import { RetailerColors } from '@/lib/constants/retailer-colors';
import { Check, X } from 'lucide-react';

interface MatchedProductCardProps {
  retailer: Retailer;
  confidence: number;
  matchType: 'exact' | 'similar';
  products: MatchedProduct[];
  onMarkCorrect: (productId: string) => void;
  onMarkIncorrect: (productId: string) => void;
}

export const MatchedProductCard: React.FC<MatchedProductCardProps> = ({
  retailer,
  confidence,
  matchType,
  products,
  onMarkCorrect,
  onMarkIncorrect,
}) => {
  const retailerName = RetailerNames[retailer];
  const headerColor = RetailerColors[retailer] || 'bg-gray-500';

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden hover:shadow-md transition-shadow">
      {/* Header with Retailer Name */}
      <div className={`${headerColor} px-4 py-3 border-b border-gray-200`}>
        <div className="flex items-center justify-between">
          <span className="font-medium text-white">
            {retailerName.en}
          </span>
          <div className="flex items-center gap-2">
            <MatchTypeBadge matchType={matchType} />
            <ConfidenceBadge confidence={confidence} />
          </div>
        </div>
      </div>

      {/* Products */}
      <div className="divide-y divide-gray-100">
        {products.map((product) => (
          <ProductItem
            key={product.id}
            product={product}
            retailerName={retailerName.en}
            onMarkCorrect={onMarkCorrect}
            onMarkIncorrect={onMarkIncorrect}
          />
        ))}
      </div>
    </div>
  );
};

interface ProductItemProps {
  product: MatchedProduct;
  retailerName: string;
  onMarkCorrect: (productId: string) => void;
  onMarkIncorrect: (productId: string) => void;
}

const ProductItem: React.FC<ProductItemProps> = ({
  product,
  retailerName,
  onMarkCorrect,
  onMarkIncorrect,
}) => {
  const isValidated = product.validationStatus === 'correct';

  return (
    <div className="p-4">
      <div className="flex gap-4">
        {/* Product Image */}
        <div className="relative w-24 h-24 flex-shrink-0 bg-gray-100 rounded-lg overflow-hidden">
          <Image
            src={product.imageUrl || '/placeholder-product.png'}
            alt={product.name}
            fill
            className="object-contain p-2"
            sizes="96px"
          />
        </div>

        {/* Product Info */}
        <div className="flex-1 min-w-0 space-y-2">
          {/* Name with validation badge */}
          <div className="flex items-start gap-2">
            <h4 className="font-medium text-gray-900 line-clamp-2 text-sm flex-1">
              {product.name}
            </h4>
            {isValidated && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 border border-green-200 flex-shrink-0">
                <Check className="w-3 h-3" />
                Verified
              </span>
            )}
            {product.isManualEntry && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800 border border-purple-200 flex-shrink-0">
                Manual
              </span>
            )}
          </div>

          {/* Details */}
          <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
            <div>
              <span className="text-gray-500">SKU:</span>
              <span className="ml-1 text-gray-700">{product.sku}</span>
            </div>
            {product.brand && (
              <div>
                <span className="text-gray-500">Brand:</span>
                <span className="ml-1 text-gray-700">{product.brand}</span>
              </div>
            )}
            {product.category && (
              <div>
                <span className="text-gray-500">Category:</span>
                <span className="ml-1 text-gray-700">{product.category}</span>
              </div>
            )}
          </div>

          {/* Price */}
          <div className="flex items-center justify-between pt-2">
            <span className="text-lg font-bold text-gray-900">
              {formatCurrency(product.price)}
            </span>

            {/* Collected Badge */}
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 border border-blue-200">
              <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                  clipRule="evenodd"
                />
              </svg>
              Collected
            </span>
          </div>
        </div>
      </div>

      {/* Product URL */}
      {product.url && (
        <a
          href={product.url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-3 inline-flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800 hover:underline"
          aria-label={`View product on ${retailerName} (opens in new tab)`}
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
              d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
            />
          </svg>
          View on {retailerName}
        </a>
      )}

      {/* Validation Action Buttons */}
      {!isValidated && (
        <div className="flex justify-end gap-2 mt-3 pt-3 border-t border-gray-100">
          <button
            onClick={() => onMarkIncorrect(product.id)}
            className="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
          >
            <X className="w-4 h-4" />
            Incorrect
          </button>
          <button
            onClick={() => onMarkCorrect(product.id)}
            className="flex items-center gap-1 px-3 py-1.5 text-sm text-green-600 hover:bg-green-50 rounded-lg transition-colors"
          >
            <Check className="w-4 h-4" />
            Correct
          </button>
        </div>
      )}
    </div>
  );
};
