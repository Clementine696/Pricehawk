'use client';

import React from 'react';
import { ArrowLeft, Check, ExternalLink } from 'lucide-react';
import { COMPETITORS, THAI_WATSADU_COLOR } from '@/lib/constants/competitors';
import { CompetitorRetailer } from '@/lib/types/manual-comparison';
import Image from 'next/image';

interface ThaiWatsuduInput {
  sku: string;
  url: string;
}

interface CompetitorEntry {
  id: string;
  retailer: string;
  url: string;
}

interface ReviewConfirmPanelProps {
  thaiWatsuduInput: ThaiWatsuduInput;
  competitorEntries: CompetitorEntry[];
  onEdit: () => void;
  onConfirm: () => void;
}

export function ReviewConfirmPanel({
  thaiWatsuduInput,
  competitorEntries,
  onEdit,
  onConfirm,
}: ReviewConfirmPanelProps) {
  const truncateUrl = (url: string, maxLength: number = 50) => {
    if (url.length <= maxLength) return url;
    return url.substring(0, maxLength) + '...';
  };

  return (
    <div className="mx-auto max-w-4xl space-y-8">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-3xl font-bold text-gray-900">
          Review Your Comparison
        </h2>
        <p className="mt-2 text-gray-600">
          Verify all details before proceeding with the comparison
        </p>
      </div>

      {/* Summary Card */}
      <div className="rounded-xl border-2 border-cyan-200 bg-gradient-to-br from-cyan-50 to-teal-50 p-6 shadow-lg">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 rounded-full bg-cyan-500 flex items-center justify-center shadow-md">
            <Check className="w-7 h-7 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-gray-900">Ready to Compare</h3>
            <p className="text-sm text-gray-600">
              1 Thai Watsadu product vs {competitorEntries.length} competitor{competitorEntries.length > 1 ? 's' : ''}
            </p>
          </div>
        </div>
      </div>

      {/* Thai Watsadu Card - Enhanced */}
      <div className="rounded-xl overflow-hidden shadow-lg border-2 border-red-300 bg-gradient-to-br from-red-50 to-red-100">
        {/* Header with brand color */}
        <div
          className="px-6 py-4 flex items-center gap-3"
          style={{ backgroundColor: THAI_WATSADU_COLOR }}
        >
          <Image
            src="/logos/thaiwatsadu.svg"
            alt="Thai Watsadu"
            width={32}
            height={32}
            className="object-contain"
          />
          <div>
            <h3 className="text-lg font-bold text-white">
              Thai Watsadu
            </h3>
            <p className="text-xs text-red-100">Source Product</p>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 bg-white space-y-4">
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 w-16 text-xs font-semibold text-gray-500 uppercase">SKU</div>
            <div className="flex-1">
              <span className="text-base font-mono font-semibold text-gray-900 bg-gray-100 px-3 py-1 rounded">
                {thaiWatsuduInput.sku}
              </span>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 w-16 text-xs font-semibold text-gray-500 uppercase">URL</div>
            <div className="flex-1">
              <a
                href={thaiWatsuduInput.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-cyan-600 hover:text-cyan-700 flex items-center gap-2 hover:underline break-all"
                title={thaiWatsuduInput.url}
              >
                <span>{truncateUrl(thaiWatsuduInput.url, 60)}</span>
                <ExternalLink className="w-4 h-4 flex-shrink-0" />
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* Competitors Card - Enhanced */}
      <div className="rounded-xl border-2 border-gray-300 bg-white shadow-lg overflow-hidden">
        <div className="px-6 py-4 bg-gradient-to-r from-gray-50 to-gray-100 border-b-2 border-gray-200">
          <h3 className="text-lg font-bold text-gray-900">
            Competitor Products ({competitorEntries.length})
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            Comparing against these retailers
          </p>
        </div>

        <div className="p-6 space-y-4">
          {competitorEntries.map((entry, index) => {
            const competitor = COMPETITORS[entry.retailer as CompetitorRetailer];
            return (
              <div
                key={entry.id}
                className="rounded-lg overflow-hidden border-2 transition-shadow hover:shadow-md"
                style={{ borderColor: competitor.color }}
              >
                {/* Competitor Header */}
                <div
                  className="px-4 py-3 flex items-center gap-3"
                  style={{ backgroundColor: `${competitor.color}15` }}
                >
                  <div className="w-8 h-8 rounded-full bg-cyan-500 flex items-center justify-center font-bold text-sm text-white shadow-sm">
                    {index + 1}
                  </div>
                  {competitor.logo && (
                    <Image
                      src={competitor.logo}
                      alt={competitor.name}
                      width={28}
                      height={28}
                      className="object-contain"
                    />
                  )}
                  <div>
                    <div className="font-bold text-gray-900">{competitor.name}</div>
                    <div className="text-xs text-gray-600">{competitor.nameTh}</div>
                  </div>
                </div>

                {/* Competitor URL */}
                <div className="px-4 py-3 bg-white">
                  <a
                    href={entry.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-cyan-600 hover:text-cyan-700 flex items-center gap-2 hover:underline break-all"
                    title={entry.url}
                  >
                    <span>{truncateUrl(entry.url, 60)}</span>
                    <ExternalLink className="w-4 h-4 flex-shrink-0" />
                  </a>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row justify-between gap-4 pt-4">
        <button
          onClick={onEdit}
          className="flex items-center justify-center gap-2 rounded-xl border-2 border-gray-300 bg-white px-8 py-4 text-gray-700 font-semibold transition-all hover:bg-gray-50 hover:shadow-md hover:scale-105 active:scale-95"
        >
          <ArrowLeft className="h-5 w-5" />
          Back to Edit
        </button>
        <button
          onClick={onConfirm}
          className="flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 px-10 py-4 font-bold text-white text-lg shadow-lg transition-all hover:from-cyan-600 hover:to-blue-600 hover:shadow-xl hover:scale-105 active:scale-95"
        >
          <Check className="h-6 w-6" />
          Confirm & Compare
        </button>
      </div>
    </div>
  );
}
