'use client';

import { CompetitorMatchResult, CompetitorRetailer } from '@/lib/types/manual-comparison';
import { COMPETITORS } from '@/lib/constants/competitors';
import { getConfidenceColor, getMatchStatusColor, formatThaiPrice } from '@/lib/utils/comparison-utils';
import { Check, X, ExternalLink, AlertCircle, Loader2 } from 'lucide-react';

interface ComparisonResultCardProps {
  result: CompetitorMatchResult;
  onConfirm: (competitor: CompetitorRetailer) => void;
  onReject: (competitor: CompetitorRetailer) => void;
  disabled?: boolean;
}

export function ComparisonResultCard({
  result,
  onConfirm,
  onReject,
  disabled = false,
}: ComparisonResultCardProps) {
  const competitor = COMPETITORS[result.competitor];
  const statusColors = getMatchStatusColor(result.status);
  const confidenceColor = getConfidenceColor(result.confidence);

  const isVerified = result.userVerified !== undefined;
  const isMatch = result.status === 'match';
  const isPending = result.status === 'pending';
  const isError = result.status === 'error';

  return (
    <div className={`border rounded-lg overflow-hidden ${statusColors.border}`}>
      {/* Header */}
      <div className={`px-4 py-3 ${statusColors.bg} border-b ${statusColors.border}`}>
        <div className="flex items-center justify-between">
          <div>
            <h4 className="font-medium text-gray-900">{competitor.name}</h4>
            <p className="text-xs text-gray-500">{competitor.domain}</p>
          </div>
          {!isPending && !isError && (
            <span className={`px-2 py-1 text-xs font-medium rounded-full ${confidenceColor}`}>
              {result.confidence}% confidence
            </span>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="p-4 bg-white">
        {isPending && (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 text-sky-500 animate-spin" />
            <span className="ml-2 text-sm text-gray-500">Processing...</span>
          </div>
        )}

        {isError && (
          <div className="flex items-center gap-2 py-4 text-red-600">
            <AlertCircle className="w-5 h-5" />
            <span className="text-sm">{result.errorMessage || 'An error occurred'}</span>
          </div>
        )}

        {!isPending && !isError && result.matchedProduct && (
          <div className="space-y-3">
            {/* Matched Product URL */}
            <a
              href={result.matchedProduct.productUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="block text-sm text-sky-600 hover:text-sky-700 hover:underline break-all"
            >
              {result.matchedProduct.productUrl}
              <ExternalLink className="w-3 h-3 inline ml-1" />
            </a>

            {/* Matched Product Details */}
            <div className="bg-gray-50 rounded-lg p-3 space-y-2">
              <p className="text-sm font-medium text-gray-900">{result.matchedProduct.name}</p>
              <div className="flex items-center gap-4 text-sm">
                <span className="text-gray-500">SKU: <span className="font-mono text-gray-900">{result.matchedProduct.sku}</span></span>
                <span className="text-gray-500">Price: <span className="font-medium text-sky-600">{formatThaiPrice(result.matchedProduct.price)}</span></span>
              </div>
            </div>
          </div>
        )}

        {!isPending && !isError && !result.matchedProduct && result.status === 'not_match' && (
          <div className="py-4 text-center text-gray-500">
            <p className="text-sm">No matching product found</p>
          </div>
        )}

        {/* Action Buttons */}
        {!isPending && !isError && (
          <div className="flex items-center gap-2 mt-4 pt-4 border-t border-gray-100">
            {isVerified ? (
              <div className={`flex items-center gap-2 px-4 py-2 rounded-lg ${
                result.userVerified ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
              }`}>
                {result.userVerified ? (
                  <>
                    <Check className="w-4 h-4" />
                    <span className="text-sm font-medium">Confirmed as Match</span>
                  </>
                ) : (
                  <>
                    <X className="w-4 h-4" />
                    <span className="text-sm font-medium">Marked as Incorrect</span>
                  </>
                )}
              </div>
            ) : (
              <>
                <button
                  type="button"
                  onClick={() => onConfirm(result.competitor)}
                  disabled={disabled}
                  className="flex items-center gap-2 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <Check className="w-4 h-4" />
                  <span className="text-sm font-medium">Match</span>
                </button>
                <button
                  type="button"
                  onClick={() => onReject(result.competitor)}
                  disabled={disabled}
                  className="flex items-center gap-2 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <X className="w-4 h-4" />
                  <span className="text-sm font-medium">Not Match</span>
                </button>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
