import React from 'react';
import Image from 'next/image';
import { ProductComparison, Retailer, RetailerNames } from '@/lib/types/price-comparison';
import { formatCurrency } from '@/lib/utils/price-utils';

interface ProductDetailCardProps {
  product: ProductComparison;
}

export const ProductDetailCard: React.FC<ProductDetailCardProps> = ({ product }) => {
  const thaiWatsaduPrice = product.prices[Retailer.THAI_WATSADU];

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="bg-blue-600 px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="bg-white text-blue-600 px-2 py-0.5 rounded text-xs font-semibold">
            My Product
          </span>
          <span className="text-white text-sm font-medium">
            {RetailerNames[Retailer.THAI_WATSADU].en}
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {/* Product Image */}
        <div className="relative w-full aspect-square bg-gray-100 rounded-lg overflow-hidden">
          <Image
            src={product.imageUrl || '/placeholder-product.png'}
            alt={product.name}
            fill
            className="object-contain p-4"
            sizes="(max-width: 768px) 100vw, 400px"
          />
        </div>

        {/* Product Info */}
        <div className="space-y-3">
          {/* Name */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 line-clamp-2">
              {product.nameTh || product.name}
            </h3>
            {product.nameTh && product.name !== product.nameTh && (
              <p className="text-sm text-gray-500 mt-1">{product.name}</p>
            )}
          </div>

          {/* Description */}
          {product.descriptionTh && (
            <p className="text-sm text-gray-600 line-clamp-3">
              {product.descriptionTh}
            </p>
          )}

          {/* Details Grid */}
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-gray-500">SKU</span>
              <p className="font-medium text-gray-900">{product.sku}</p>
            </div>
            <div>
              <span className="text-gray-500">Brand</span>
              <p className="font-medium text-gray-900">{product.brand}</p>
            </div>
            <div>
              <span className="text-gray-500">Category</span>
              <p className="font-medium text-gray-900">
                {product.categoryTh || product.category}
              </p>
            </div>
          </div>

          {/* Price */}
          <div className="pt-3 border-t border-gray-100">
            <span className="text-gray-500 text-sm">Price</span>
            <p className="text-2xl font-bold text-blue-600">
              {thaiWatsaduPrice.price !== null
                ? formatCurrency(thaiWatsaduPrice.price)
                : 'N/A'}
            </p>
          </div>

          {/* Product URL */}
          {thaiWatsaduPrice.productUrl && (
            <a
              href={thaiWatsaduPrice.productUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800 hover:underline"
              aria-label={`View product on ${RetailerNames[Retailer.THAI_WATSADU].en} (opens in new tab)`}
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
              View on Thai Watsadu
            </a>
          )}
        </div>
      </div>
    </div>
  );
};
