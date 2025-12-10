'use client';

import React from 'react';
import Image from 'next/image';
import { ComparisonStickyHeader } from './ComparisonStickyHeader';
import { ComparisonSpecSection } from './ComparisonSpecSection';
import { PriceDifferenceDisplay } from './PriceDifferenceDisplay';

interface ComparisonProduct {
  sku: string;
  name: string;
  price: number;
  discountPercentage?: number;
  unitPrice?: number;
  imageUrl?: string;
  productUrl: string;
  brand?: string;
  category?: string;
  stockStatus?: string;
  retailer: string;
  retailerLogo?: string;
}

interface AppleStyleComparisonTableProps {
  thaiWatsuduProduct: ComparisonProduct;
  competitorProducts: ComparisonProduct[];
}

export function AppleStyleComparisonTable({
  thaiWatsuduProduct,
  competitorProducts,
}: AppleStyleComparisonTableProps) {
  // Product info attributes
  const productInfoAttributes = [
    { key: 'name', label: 'Product Name', type: 'text' as const },
    { key: 'sku', label: 'SKU', type: 'text' as const },
    { key: 'brand', label: 'Brand', type: 'text' as const, showIcons: true },
    {
      key: 'category',
      label: 'Category',
      type: 'text' as const,
      showIcons: true,
    },
  ];

  // Availability attributes - only show product URL
  const availabilityAttributes = [
    { key: 'productUrl', label: 'Product Link', type: 'url' as const },
  ];

  return (
    <div className="w-full overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-sm">
      <table className="w-full table-fixed border-collapse">
        {/* Sticky Header with Product Images */}
        <ComparisonStickyHeader
          thaiWatsuduProduct={{
            imageUrl: thaiWatsuduProduct.imageUrl,
            name: thaiWatsuduProduct.name,
            retailer: 'Thai Watsadu',
            retailerLogo: thaiWatsuduProduct.retailerLogo,
          }}
          competitorProducts={competitorProducts.map((p) => ({
            imageUrl: p.imageUrl,
            name: p.name,
            retailer: p.retailer,
            retailerLogo: p.retailerLogo,
          }))}
        />

        {/* Compare Row with Product Images */}
        <tbody>
          <tr className="border-b border-gray-200">
            <td className="sticky left-0 bg-white px-6 py-4 text-sm font-medium text-gray-700">
              Compare
            </td>
            <td className="px-4 py-4 text-center">
              <div className="flex flex-col items-center gap-2">
                {thaiWatsuduProduct.imageUrl ? (
                  <div className="relative h-20 w-20">
                    <Image
                      src={thaiWatsuduProduct.imageUrl}
                      alt={thaiWatsuduProduct.name}
                      fill
                      className="object-contain"
                      sizes="80px"
                    />
                  </div>
                ) : (
                  <div className="flex h-20 w-20 items-center justify-center rounded-lg bg-gray-100">
                    <span className="text-xs text-gray-400">No image</span>
                  </div>
                )}
              </div>
            </td>
            {competitorProducts.map((competitor, index) => (
              <td key={index} className="px-4 py-4 text-center">
                <div className="flex flex-col items-center gap-2">
                  {competitor.imageUrl ? (
                    <div className="relative h-20 w-20">
                      <Image
                        src={competitor.imageUrl}
                        alt={competitor.name}
                        fill
                        className="object-contain"
                        sizes="80px"
                      />
                    </div>
                  ) : (
                    <div className="flex h-20 w-20 items-center justify-center rounded-lg bg-gray-100">
                      <span className="text-xs text-gray-400">No image</span>
                    </div>
                  )}
                </div>
              </td>
            ))}
          </tr>

          {/* PRICE COMPARISON Section Header */}
          <tr className="bg-gray-50">
            <td
              colSpan={2 + competitorProducts.length}
              className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500"
            >
              PRICE COMPARISON
            </td>
          </tr>
          <tr className="border-b border-gray-200">
            <td className="sticky left-0 bg-white px-6 py-4 text-sm font-medium text-gray-700">
              Price
            </td>
            <td className="px-6 py-4 text-center">
              <div className="text-2xl font-bold text-gray-900">
                ฿{thaiWatsuduProduct.price.toLocaleString('th-TH')}
              </div>
            </td>
            {competitorProducts.map((competitor, index) => (
              <td key={index} className="px-6 py-4 text-center">
                <PriceDifferenceDisplay
                  thaiWatsuduPrice={thaiWatsuduProduct.price}
                  competitorPrice={competitor.price}
                  competitorName={competitor.retailer}
                  showLargePrice={true}
                />
              </td>
            ))}
          </tr>
          <tr>
            <td
              colSpan={2 + competitorProducts.length}
              className="h-4 bg-white"
            ></td>
          </tr>
        </tbody>

        {/* Product Information Section */}
        <ComparisonSpecSection
          title="Product Information"
          attributes={productInfoAttributes}
          thaiWatsuduData={thaiWatsuduProduct}
          competitorData={competitorProducts}
        />

        {/* Product Links Section */}
        <ComparisonSpecSection
          title="Product Links"
          attributes={availabilityAttributes}
          thaiWatsuduData={thaiWatsuduProduct}
          competitorData={competitorProducts}
        />
      </table>
    </div>
  );
}
