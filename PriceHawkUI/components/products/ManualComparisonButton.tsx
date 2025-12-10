'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { Search } from 'lucide-react';

interface ManualComparisonButtonProps {
  productId: string;
  sku: string;
  url?: string | null;
}

export const ManualComparisonButton: React.FC<ManualComparisonButtonProps> = ({
  productId,
  sku,
  url,
}) => {
  const router = useRouter();

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent row click event from triggering
    const params = new URLSearchParams({
      sku: sku,
      productId: productId,
    });

    if (url) {
      params.set('url', url);
    }

    router.push(`/comparison?${params.toString()}`);
  };

  return (
    <button
      onClick={handleClick}
      className="inline-flex items-center gap-2 px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-cyan-500 hover:bg-cyan-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-cyan-500 transition-colors"
    >
      <Search className="w-4 h-4" />
      Manual Comparison
    </button>
  );
};
