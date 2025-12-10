'use client';

import { ThaiWatsuduInput, CompetitorUrlEntry } from '@/lib/types/manual-comparison';
import { COMPETITORS } from '@/lib/constants/competitors';
import { Edit2, ExternalLink } from 'lucide-react';
import Image from 'next/image';

interface ComparisonSummaryCardProps {
  thaiWatsadu: ThaiWatsuduInput;
  competitorEntries: CompetitorUrlEntry[];
  onEdit?: () => void;
}

export function ComparisonSummaryCard({
  thaiWatsadu,
  competitorEntries,
  onEdit,
}: ComparisonSummaryCardProps) {
  const totalUrls = competitorEntries.reduce(
    (sum, entry) => sum + entry.urls.filter(url => url.trim() !== '').length,
    0
  );

  const truncateUrl = (url: string, maxLength: number = 40) => {
    if (url.length <= maxLength) return url;
    return url.substring(0, maxLength) + '...';
  };

  return (
    <div className="bg-gradient-to-br from-gray-50 to-gray-100 border-2 border-gray-300 rounded-xl p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-bold text-gray-900">Comparison Summary</h3>
        {onEdit && (
          <button
            type="button"
            onClick={onEdit}
            className="flex items-center gap-2 text-sm text-cyan-600 hover:text-cyan-700 font-medium transition-colors"
          >
            <Edit2 className="w-4 h-4" />
            <span>Edit</span>
          </button>
        )}
      </div>

      <p className="text-sm text-gray-600">
        Review your comparison setup before proceeding
      </p>

      {/* Thai Watsadu Product */}
      <div className="bg-white rounded-lg p-4 border-2 border-red-200">
        <div className="flex items-start gap-3">
          <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center flex-shrink-0">
            <Image
              src="/logos/thaiwatsadu.svg"
              alt="Thai Watsadu"
              width={40}
              height={40}
              className="object-contain"
            />
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="text-sm font-semibold text-gray-900 mb-1">Thai Watsadu</h4>
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-xs">
                <span className="text-gray-500 font-medium">SKU:</span>
                <span className="text-gray-900 font-mono">{thaiWatsadu.sku}</span>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <span className="text-gray-500 font-medium">URL:</span>
                <a
                  href={thaiWatsadu.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-cyan-600 hover:text-cyan-700 flex items-center gap-1 truncate"
                  title={thaiWatsadu.url}
                >
                  <span className="truncate">{truncateUrl(thaiWatsadu.url)}</span>
                  <ExternalLink className="w-3 h-3 flex-shrink-0" />
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Competitors */}
      <div className="space-y-2">
        <h4 className="text-sm font-semibold text-gray-700">
          Comparing with {competitorEntries.length} {competitorEntries.length === 1 ? 'retailer' : 'retailers'}
        </h4>
        <div className="flex flex-wrap gap-2">
          {competitorEntries.map((entry) => {
            const competitor = COMPETITORS[entry.retailer];
            const validUrls = entry.urls.filter(url => url.trim() !== '');
            return (
              <div
                key={entry.id}
                className="flex items-center gap-2 px-3 py-2 bg-white rounded-lg border border-gray-200"
              >
                {competitor.logo && (
                  <Image
                    src={competitor.logo}
                    alt={competitor.name}
                    width={24}
                    height={24}
                    className="object-contain"
                  />
                )}
                <div className="flex flex-col">
                  <span className="text-sm font-medium text-gray-900">
                    {competitor.name}
                  </span>
                  <span className="text-xs text-gray-500">
                    {validUrls.length} {validUrls.length === 1 ? 'URL' : 'URLs'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Total Count */}
      <div className="pt-3 border-t border-gray-300">
        <div className="flex items-center justify-between text-sm">
          <span className="font-medium text-gray-700">Total URLs to compare:</span>
          <span className="text-lg font-bold text-cyan-600">{totalUrls}</span>
        </div>
      </div>
    </div>
  );
}
