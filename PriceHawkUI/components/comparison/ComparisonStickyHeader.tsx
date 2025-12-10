'use client';

import React from 'react';
import Image from 'next/image';

interface Product {
  imageUrl?: string;
  name: string;
  retailer: string;
  retailerLogo?: string;
}

interface ComparisonStickyHeaderProps {
  thaiWatsuduProduct: Product;
  competitorProducts: Product[];
}

export function ComparisonStickyHeader({
  thaiWatsuduProduct,
  competitorProducts,
}: ComparisonStickyHeaderProps) {
  const renderRetailerColumn = (product: Product, index: number) => {
    return (
      <th
        key={index}
        className="min-w-[180px] border-b border-gray-300 bg-white px-4 py-4"
      >
        <div className="flex justify-center">
          {product.retailerLogo ? (
            <Image
              src={product.retailerLogo}
              alt={product.retailer}
              width={100}
              height={32}
              className="object-contain"
            />
          ) : (
            <div className="text-sm font-semibold text-gray-900">
              {product.retailer}
            </div>
          )}
        </div>
      </th>
    );
  };

  return (
    <thead className="sticky top-0 z-10 shadow-sm">
      <tr>
        {/* Empty corner cell */}
        <th className="sticky left-0 z-20 min-w-[140px] border-b border-gray-300 bg-gray-50 px-6 py-4 text-left text-sm font-semibold text-gray-700">
          Compare
        </th>

        {/* Thai Watsadu Column */}
        {renderRetailerColumn(
          {
            ...thaiWatsuduProduct,
            retailer: 'Thai Watsadu',
          },
          0
        )}

        {/* Competitor Columns */}
        {competitorProducts.map((product, index) =>
          renderRetailerColumn(product, index + 1)
        )}
      </tr>
    </thead>
  );
}
