'use client';

import React, { useState } from 'react';
import { Download } from 'lucide-react';
import { ProductComparison } from '@/lib/types/price-comparison';
import { exportToCSV } from '@/lib/utils/export-utils';

interface ExportButtonProps {
  products: ProductComparison[];
  filename?: string;
}

export const ExportButton: React.FC<ExportButtonProps> = ({
  products,
  filename,
}) => {
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async () => {
    try {
      setIsExporting(true);
      exportToCSV(products, filename);
    } catch (error) {
      console.error('Export failed:', error);
      alert('Export failed. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <button
      onClick={handleExport}
      disabled={isExporting || products.length === 0}
      className="inline-flex items-center gap-2 px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-cyan-500 hover:bg-cyan-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed"
    >
      <Download className="w-4 h-4" />
      {isExporting ? 'Exporting...' : 'Export'}
    </button>
  );
};
