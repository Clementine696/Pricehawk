'use client';

import Image from 'next/image';
import { SourceProduct } from '@/lib/types/manual-comparison';
import { formatThaiPrice } from '@/lib/utils/comparison-utils';
import { ExternalLink, Package } from 'lucide-react';

interface SourceProductCardProps {
  product: SourceProduct;
}

export function SourceProductCard({ product }: SourceProductCardProps) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="bg-sky-50 px-4 py-2 border-b border-sky-100">
        <span className="text-sm font-semibold text-sky-700">INPUT</span>
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Product Image */}
        <div className="relative w-full aspect-square bg-gray-100 rounded-lg overflow-hidden mb-4">
          {product.imageUrl ? (
            <Image
              src={product.imageUrl}
              alt={product.name}
              fill
              className="object-contain"
              sizes="(max-width: 768px) 100vw, 300px"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <Package className="w-16 h-16 text-gray-300" />
            </div>
          )}
        </div>

        {/* Product Info */}
        <div className="space-y-3">
          <div>
            <p className="text-sm text-gray-500">Product name</p>
            <p className="font-medium text-gray-900">{product.name}</p>
            {product.nameTh && (
              <p className="text-sm text-gray-600">{product.nameTh}</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <p className="text-sm text-gray-500">SKU</p>
              <p className="font-mono text-sm font-medium text-gray-900">{product.sku}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Price</p>
              <p className="font-medium text-sky-600">{formatThaiPrice(product.price)}</p>
            </div>
          </div>

          {(product.category || product.brand) && (
            <div className="grid grid-cols-2 gap-3">
              {product.category && (
                <div>
                  <p className="text-sm text-gray-500">Category</p>
                  <p className="text-sm text-gray-900">{product.category}</p>
                </div>
              )}
              {product.brand && (
                <div>
                  <p className="text-sm text-gray-500">Brand</p>
                  <p className="text-sm text-gray-900">{product.brand}</p>
                </div>
              )}
            </div>
          )}

          {/* Link to Product */}
          <a
            href={product.productUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-sm text-sky-600 hover:text-sky-700"
          >
            <span>More info on Product listing</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>
    </div>
  );
}
