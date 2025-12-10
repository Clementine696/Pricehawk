'use client';

import React from 'react';
import { Check, Minus, AlertTriangle, ExternalLink } from 'lucide-react';
import { formatThaiCurrency } from '@/lib/utils/comparison-display-utils';

interface ComparisonAttributeRowProps {
  label: string;
  thaiWatsuduValue: any;
  competitorValues: any[];
  attributeType?: 'text' | 'price' | 'status' | 'url';
  showIcons?: boolean;
}

export function ComparisonAttributeRow({
  label,
  thaiWatsuduValue,
  competitorValues,
  attributeType = 'text',
  showIcons = false,
}: ComparisonAttributeRowProps) {
  const formatValue = (value: any): React.ReactNode => {
    if (value === null || value === undefined || value === '') {
      return (
        <span className="flex items-center justify-center text-gray-400">
          <Minus className="h-4 w-4" />
        </span>
      );
    }

    switch (attributeType) {
      case 'price':
        return (
          <span className="font-semibold text-gray-900">
            {formatThaiCurrency(value)}
          </span>
        );
      case 'url':
        return (
          <a
            href={value}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-700 hover:underline"
          >
            View Product
            <ExternalLink className="h-3 w-3" />
          </a>
        );
      case 'status':
        return (
          <span className="rounded-full bg-gray-100 px-2 py-1 text-xs font-medium text-gray-700">
            {value}
          </span>
        );
      case 'text':
      default:
        return <span className="text-gray-900">{value}</span>;
    }
  };

  const getMatchIcon = (value: any, compareValue: any) => {
    if (
      value === null ||
      value === undefined ||
      value === '' ||
      compareValue === null ||
      compareValue === undefined ||
      compareValue === ''
    ) {
      return null;
    }

    const isMatch =
      String(value).toLowerCase() === String(compareValue).toLowerCase();

    if (isMatch) {
      return <Check className="ml-2 h-4 w-4 text-green-600" />;
    }

    if (attributeType === 'price') {
      return <AlertTriangle className="ml-2 h-4 w-4 text-amber-600" />;
    }

    return null;
  };

  return (
    <tr className="border-b border-gray-200 hover:bg-gray-50">
      {/* Label Column */}
      <td className="sticky left-0 bg-white px-6 py-4 text-sm font-medium text-gray-700">
        {label}
      </td>

      {/* Thai Watsadu Column */}
      <td className="px-6 py-4 text-center text-sm">
        {formatValue(thaiWatsuduValue)}
      </td>

      {/* Competitor Columns */}
      {competitorValues.map((value, index) => (
        <td key={index} className="px-6 py-4 text-center text-sm">
          <div className="flex items-center justify-center">
            {formatValue(value)}
            {showIcons && getMatchIcon(value, thaiWatsuduValue)}
          </div>
        </td>
      ))}
    </tr>
  );
}
